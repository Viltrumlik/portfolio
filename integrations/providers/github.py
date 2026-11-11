"""GitHub: verify a token, mirror public repos + contributions, and turn activity into events."""
import time
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from automations.events import emit
from automations.models import Event

from .. import http
from ..errors import AuthError, Permanent, RateLimited, Transient
from ..health import record_success
from ..models import Connection, ContributionDay, Repo, SyncRun

API = "https://api.github.com"
GRAPHQL = f"{API}/graphql"
SERVICE = "GitHub"
SYNC_EVERY = timedelta(hours=1)
STACK_SIZE = 5

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

VERIFY_QUERY = "query { viewer { login } }"

PROFILE_QUERY = """
query {
  viewer {
    login
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { databaseId } } }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

REPOS_QUERY = """
query($after: String) {
  viewer {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        databaseId name nameWithOwner description url homepageUrl
        stargazerCount forkCount isFork isArchived pushedAt
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
        repositoryTopics(first: 20) { nodes { topic { name } } }
      }
    }
  }
}
"""


# --- HTTP ---------------------------------------------------------------------------


def _headers(token, extra=None):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", **(extra or {})}


def _raise_for(response):
    status = response.status_code
    if status in (200, 304):
        return
    if status == 401:
        raise AuthError("GitHub rejected the token. Create a new token and reconnect.", code="401")
    if status in (403, 429):
        if response.headers.get("Retry-After"):
            raise RateLimited(int(response.headers["Retry-After"]), "GitHub asked us to slow down.", code=str(status))
        if response.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(response.headers.get("X-RateLimit-Reset") or 0)
            raise RateLimited(max(1, reset - int(time.time())), "GitHub's rate limit is used up; syncing resumes after it resets.", code=str(status))
        raise Permanent(f"GitHub refused access ({status}). Check the token's permissions.", code=str(status))
    if status >= 500:
        raise Transient(f"GitHub is having trouble ({status}). It will retry.", code=str(status))
    raise Permanent(f"GitHub answered {status}.", code=str(status))


def _graphql(token, query, variables=None):
    response = http.request("POST", GRAPHQL, service=SERVICE, headers=_headers(token), json={"query": query, "variables": variables or {}})
    _raise_for(response)
    body = response.json()
    errors = body.get("errors") or []
    if any(e.get("type") == "RATE_LIMITED" for e in errors):
        raise RateLimited(60, "GitHub's rate limit is used up; syncing resumes after it resets.", code="RATE_LIMITED")
    if errors:
        raise Permanent(f"GitHub could not answer: {errors[0].get('message', 'unknown error')}", code=errors[0].get("type", "graphql"))
    if not body.get("data"):
        raise Permanent("GitHub returned no data.", code="graphql")
    return body["data"], response


# --- verify -------------------------------------------------------------------------


def verify(token):
    """Check a token. Returns {"login", "scopes"} (scopes from X-OAuth-Scopes; fine-grained tokens have none)."""
    data, response = _graphql(token, VERIFY_QUERY)
    header = response.headers.get("X-OAuth-Scopes", "")
    return {"login": data["viewer"]["login"], "scopes": [s.strip() for s in header.split(",") if s.strip()]}


# --- full sync ----------------------------------------------------------------------


def full_sync(connection):
    """Mirror public owned repos, pinned repos and the contribution calendar; upsert Projects."""
    run = SyncRun.objects.create(connection=connection, kind="full")
    try:
        token = connection.credentials["token"]
        profile, _ = _graphql(token, PROFILE_QUERY)
        nodes = _all_repos(token)
        viewer = profile["viewer"]
        pinned = {n["databaseId"] for n in viewer["pinnedItems"]["nodes"] if n and n.get("databaseId")}
        days = [d for week in viewer["contributionsCollection"]["contributionCalendar"]["weeks"] for d in week["contributionDays"]]
        with transaction.atomic():
            changed = _upsert_repos(nodes, pinned)
            changed += _upsert_days(days)
            changed += _upsert_projects(Repo.objects.filter(is_fork=False, is_archived=False))
    except Exception as exc:
        SyncRun.objects.filter(pk=run.pk).update(status=SyncRun.Status.FAILED, message=str(exc), finished_at=timezone.now())
        raise
    SyncRun.objects.filter(pk=run.pk).update(status=SyncRun.Status.OK, items_changed=changed, finished_at=timezone.now())
    record_success(connection)  # status connected, error cleared, last_synced_at now
    connection.account, connection.next_sync_at = viewer["login"], connection.last_synced_at + SYNC_EVERY
    Connection.objects.filter(pk=connection.pk).update(account=connection.account, next_sync_at=connection.next_sync_at)
    return changed


def _all_repos(token):
    nodes, after = [], None
    while True:
        data, _ = _graphql(token, REPOS_QUERY, {"after": after})
        page = data["viewer"]["repositories"]
        nodes.extend(n for n in page["nodes"] if n)
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        after = page["pageInfo"]["endCursor"]


def _repo_fields(node, pinned):
    languages = {e["node"]["name"]: e["size"] for e in (node.get("languages") or {}).get("edges", [])}
    return {
        "name": node["name"],
        "full_name": node["nameWithOwner"],
        "description": node.get("description") or "",
        "url": node["url"],
        "homepage": node.get("homepageUrl") or "",
        "language": (node.get("primaryLanguage") or {}).get("name", ""),
        "languages": languages,
        "stars": node.get("stargazerCount") or 0,
        "forks": node.get("forkCount") or 0,
        "topics": [t["topic"]["name"] for t in (node.get("repositoryTopics") or {}).get("nodes", [])],
        "is_fork": bool(node.get("isFork")),
        "is_archived": bool(node.get("isArchived")),
        "pinned": node["databaseId"] in pinned,
        "pushed_at": parse_datetime(node["pushedAt"]) if node.get("pushedAt") else None,
    }


def _upsert_repos(nodes, pinned):
    changed = 0
    existing = {r.github_id: r for r in Repo.objects.all()}
    seen = set()
    for node in nodes:
        fields = _repo_fields(node, pinned)
        github_id = node["databaseId"]
        seen.add(github_id)
        repo = existing.get(github_id)
        if repo is None:
            # A different repo may hold this full name (deleted and recreated): free the name first.
            Repo.objects.filter(full_name=fields["full_name"]).exclude(github_id=github_id).delete()
            Repo.objects.create(github_id=github_id, **fields)
            changed += 1
        elif any(getattr(repo, k) != v for k, v in fields.items()):
            for k, v in fields.items():
                setattr(repo, k, v)
            repo.save()
            changed += 1
    gone = Repo.objects.exclude(github_id__in=seen)
    changed += gone.count()
    gone.delete()  # deleted or made private: stop showing it
    return changed


def _upsert_days(days):
    existing = {d.date.isoformat(): d for d in ContributionDay.objects.all()}
    create, update = [], []
    for day in days:
        count, level = day["contributionCount"], LEVELS.get(day["contributionLevel"], 0)
        row = existing.get(day["date"])
        if row is None:
            create.append(ContributionDay(date=day["date"], count=count, level=level))
        elif (row.count, row.level) != (count, level):
            row.count, row.level = count, level
            update.append(row)
    ContributionDay.objects.bulk_create(create)
    ContributionDay.objects.bulk_update(update, ["count", "level"])
    return len(create) + len(update)


def _top_languages(repo):
    return [name for name, _ in sorted(repo.languages.items(), key=lambda kv: -kv[1])][:STACK_SIZE]


def _unique_slug(name):
    from content.models import Project

    base = (slugify(name) or "project")[:200]
    slug, n = base, 2
    while Project.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _upsert_projects(repos):
    """Create a Project per repo; link and fill gaps, never overwrite curated text."""
    from content.models import Project

    changed = 0
    for repo in repos:
        project = Project.objects.filter(repo=repo).first() or Project.objects.filter(repo_full_name=repo.full_name).first()
        if project is None:
            Project.objects.create(
                repo_full_name=repo.full_name,
                repo=repo,
                slug=_unique_slug(repo.name),
                summary=repo.description,
                stack=_top_languages(repo),
            )
            changed += 1
            continue
        dirty = []
        if project.repo_full_name != repo.full_name and not Project.objects.filter(repo_full_name=repo.full_name).exists():
            project.repo_full_name = repo.full_name  # the repo was renamed: keep the curated project
            dirty.append("repo_full_name")
        if project.repo_id != repo.pk:
            project.repo = repo
            dirty.append("repo")
        if not project.summary and repo.description:
            project.summary = repo.description
            dirty.append("summary")
        if not project.stack and repo.languages:
            project.stack = _top_languages(repo)
            dirty.append("stack")
        if dirty:
            project.save(update_fields=[*dirty, "updated_at"])
            changed += 1
    return changed


# --- public events ------------------------------------------------------------------


def poll_events(connection):
    """Turn new public PushEvents and published releases into events. Uses an ETag (304 = nothing new)."""
    login = connection.account
    if not login:
        raise Permanent("The GitHub account is unknown. Reconnect GitHub.", code="account")
    config = dict(connection.config or {})
    first_poll = "events_etag" not in config
    headers = _headers(connection.credentials["token"])
    if config.get("events_etag"):
        headers["If-None-Match"] = config["events_etag"]
    response = http.request("GET", f"{API}/users/{login}/events/public", service=SERVICE, headers=headers, params={"per_page": 30})
    _raise_for(response)
    if response.status_code == 304:
        return 0
    emitted = 0
    for item in reversed(response.json() or []):
        event = _emit_public_event(item)
        if event is not None:
            emitted += 1
            if first_poll:  # history from before the connection: show it, but don't run rules on it
                Event.objects.filter(pk=event.pk, dispatched_at__isnull=True).update(dispatched_at=timezone.now())
    config["events_etag"] = response.headers.get("ETag", "")
    Connection.objects.filter(pk=connection.pk).update(config=config)
    connection.config = config
    return emitted


def push_payload(repo, ref, head, before=None, commits=None, url=None):
    """The github.push payload, or None for tag pushes and deleted branches."""
    if not ref or not ref.startswith("refs/heads/") or not head or set(head) == {"0"}:
        return None
    if not url:
        if before and set(before) != {"0"}:
            url = f"https://github.com/{repo}/compare/{before}...{head}"
        else:
            url = f"https://github.com/{repo}/commit/{head}"
    return {"repo": repo, "branch": ref[len("refs/heads/"):], "commits": commits, "url": url, "head": head}


def release_payload(repo, release):
    return {"repo": repo, "tag": release.get("tag_name", ""), "name": release.get("name") or "", "url": release.get("html_url", "")}


def already_recorded(type, payload):
    """Same push (by head) or release (by tag) already stored from the webhook or the poll."""
    if type == "github.push":
        return Event.objects.filter(type=type, payload__repo=payload["repo"], payload__head=payload["head"]).exists()
    return Event.objects.filter(type=type, payload__repo=payload["repo"], payload__tag=payload["tag"]).exists()


def _emit_public_event(item):
    repo = (item.get("repo") or {}).get("name", "")
    payload = item.get("payload") or {}
    if item.get("type") == "PushEvent":
        commits = payload.get("size")
        if commits is None and isinstance(payload.get("commits"), list):
            commits = len(payload["commits"])
        data, type = push_payload(repo, payload.get("ref"), payload.get("head"), payload.get("before"), commits), "github.push"
    elif item.get("type") == "ReleaseEvent" and payload.get("action") == "published":
        data, type = release_payload(repo, payload.get("release") or {}), "github.release.published"
    else:
        return None
    external_id = f"gh-{item['id']}"
    if data is None or Event.objects.filter(external_id=external_id).exists() or already_recorded(type, data):
        return None
    return emit(type, data, source="github", external_id=external_id, public=True, occurred_at=parse_datetime(item.get("created_at") or "") or timezone.now())
