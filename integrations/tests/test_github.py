from datetime import timedelta

import httpx
import pytest
from django.utils import timezone

from automations.models import Event
from content.models import Project
from integrations.errors import AuthError, Permanent, RateLimited, Transient
from integrations.models import Connection, ContributionDay, Repo, SyncRun
from integrations.providers import github
from integrations.tests.github_data import GRAPHQL, install_graphql, repo_node, repos_page, viewer_profile

pytestmark = pytest.mark.django_db


@pytest.fixture
def conn():
    return Connection.objects.create(provider="github", status="syncing", account="A1isherDev", credentials={"token": "ghp_test"})


# --- verify -------------------------------------------------------------------


def test_verify_returns_login_and_scopes(api):
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}}, headers={"X-OAuth-Scopes": "public_repo, read:user"})
    assert github.verify("ghp_test") == {"login": "A1isherDev", "scopes": ["public_repo", "read:user"]}
    assert api.requests[0].headers["Authorization"] == "Bearer ghp_test"


def test_verify_without_scopes_header_returns_no_scopes(api):
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}})
    assert github.verify("github_pat_x")["scopes"] == []


def test_rejected_token_is_an_auth_error(api):
    api.add("POST", GRAPHQL, status=401, json={"message": "Bad credentials"})
    with pytest.raises(AuthError, match="GitHub rejected the token"):
        github.verify("bad")


def test_exhausted_rate_limit_is_rate_limited(api):
    reset = int((timezone.now() + timedelta(seconds=120)).timestamp())
    api.add("POST", GRAPHQL, status=403, json={"message": "rate limit"}, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)})
    with pytest.raises(RateLimited) as info:
        github.verify("t")
    assert 100 <= info.value.retry_after_seconds <= 121


def test_server_errors_are_transient(api):
    api.add("POST", GRAPHQL, status=502, json={})
    with pytest.raises(Transient):
        github.verify("t")


def test_graphql_errors_are_permanent(api):
    api.add("POST", GRAPHQL, json={"errors": [{"type": "NOT_FOUND", "message": "Could not resolve"}]})
    with pytest.raises(Permanent):
        github.verify("t")


def test_graphql_rate_limit_error_is_rate_limited(api):
    api.add("POST", GRAPHQL, json={"errors": [{"type": "RATE_LIMITED", "message": "API rate limit exceeded"}]})
    with pytest.raises(RateLimited):
        github.verify("t")


# --- full sync ------------------------------------------------------------------


def test_full_sync_stores_repos_contributions_and_projects(api, conn):
    install_graphql(
        api,
        repos_pages=[
            repos_page(
                [
                    repo_node(1, "atlas", description="My portfolio.", languages=[("Python", 9000), ("CSS", 500)], topics=["django"]),
                    repo_node(2, "forked", fork=True),
                    repo_node(3, "old", archived=True),
                ]
            )
        ],
        profile=viewer_profile(pinned_ids=[1]),
    )

    github.full_sync(conn)

    atlas = Repo.objects.get(github_id=1)
    assert atlas.full_name == "A1isherDev/atlas"
    assert atlas.description == "My portfolio."
    assert atlas.language == "Python"
    assert atlas.languages == {"Python": 9000, "CSS": 500}
    assert atlas.topics == ["django"]
    assert atlas.pinned is True
    assert atlas.pushed_at is not None
    assert Repo.objects.get(github_id=2).pinned is False

    assert {d.date.isoformat(): (d.count, d.level) for d in ContributionDay.objects.all()} == {
        "2026-11-08": (0, 0),
        "2026-11-09": (4, 2),
        "2026-11-10": (12, 4),
    }

    project = Project.objects.get()
    assert project.repo_full_name == "A1isherDev/atlas"
    assert project.repo == atlas
    assert project.slug == "atlas"
    assert project.summary == "My portfolio."
    assert project.stack == ["Python", "CSS"]
    assert project.title == ""

    run = SyncRun.objects.get()
    assert run.status == SyncRun.Status.OK
    assert run.items_changed > 0

    conn.refresh_from_db()
    assert conn.status == Connection.Status.CONNECTED
    assert conn.last_synced_at is not None
    assert conn.next_sync_at - conn.last_synced_at == timedelta(hours=1)
    assert conn.account == "A1isherDev"


def test_full_sync_never_overwrites_curated_project_fields(api, conn):
    Project.objects.create(
        repo_full_name="A1isherDev/atlas", slug="my-site", title="Atlas", summary="Curated.", case_study="Long", kind="Platform", stack=["Django"]
    )
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas", description="From GitHub.")])], profile=viewer_profile())

    github.full_sync(conn)

    project = Project.objects.get()
    assert (project.slug, project.title, project.summary, project.case_study, project.kind, project.stack) == (
        "my-site", "Atlas", "Curated.", "Long", "Platform", ["Django"]
    )
    assert project.repo == Repo.objects.get(github_id=1)


def test_full_sync_fills_only_empty_summary_and_stack(api, conn):
    Project.objects.create(repo_full_name="A1isherDev/atlas", slug="atlas", summary="", stack=[])
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas", description="From GitHub.")])], profile=viewer_profile())
    github.full_sync(conn)
    project = Project.objects.get()
    assert project.summary == "From GitHub."
    assert project.stack == ["Python", "HTML"]


def test_new_project_slugs_are_unique(api, conn):
    Project.objects.create(repo_full_name="someone/atlas", slug="atlas")
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas")])], profile=viewer_profile())
    github.full_sync(conn)
    assert Project.objects.get(repo_full_name="A1isherDev/atlas").slug == "atlas-2"


def test_renamed_repo_keeps_its_curated_project(api, conn):
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas")])], profile=viewer_profile())
    github.full_sync(conn)
    Project.objects.update(title="Atlas")

    api.routes.clear()
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas-os")])], profile=viewer_profile())
    github.full_sync(conn)

    project = Project.objects.get()
    assert project.repo_full_name == "A1isherDev/atlas-os"
    assert project.title == "Atlas"


def test_full_sync_follows_pagination_and_drops_repos_that_are_gone(api, conn):
    Repo.objects.create(github_id=99, name="private-now", full_name="A1isherDev/private-now", url="https://github.com/A1isherDev/private-now")
    install_graphql(
        api,
        repos_pages=[repos_page([repo_node(1, "a")], next_cursor="1"), repos_page([repo_node(2, "b")])],
        profile=viewer_profile(),
    )
    github.full_sync(conn)
    assert set(Repo.objects.values_list("github_id", flat=True)) == {1, 2}


def test_unchanged_second_sync_changes_nothing(api, conn):
    install_graphql(api, repos_pages=[repos_page([repo_node(1, "atlas")])], profile=viewer_profile())
    github.full_sync(conn)
    github.full_sync(conn)
    assert SyncRun.objects.order_by("started_at", "id").last().items_changed == 0


def test_failed_full_sync_records_a_failed_run(api, conn):
    api.add("POST", GRAPHQL, status=401, json={})
    with pytest.raises(AuthError):
        github.full_sync(conn)
    run = SyncRun.objects.get()
    assert run.status == SyncRun.Status.FAILED
    assert "rejected" in run.message


# --- public events ------------------------------------------------------------------

EVENTS_URL = "https://api.github.com/users/A1isherDev/events/public"


def push_event(event_id, *, head="abc123", ref="refs/heads/main", size=2, repo="A1isherDev/atlas"):
    return {
        "id": str(event_id),
        "type": "PushEvent",
        "repo": {"name": repo},
        "payload": {"ref": ref, "head": head, "before": "000111", "size": size},
        "created_at": "2026-11-10T10:00:00Z",
    }


def release_event(event_id, *, action="published"):
    return {
        "id": str(event_id),
        "type": "ReleaseEvent",
        "repo": {"name": "A1isherDev/atlas"},
        "payload": {"action": action, "release": {"tag_name": "v1.2.0", "name": "Spring", "html_url": "https://github.com/A1isherDev/atlas/releases/tag/v1.2.0"}},
        "created_at": "2026-11-10T11:00:00Z",
    }


def test_poll_events_emits_push_and_release_events(api, conn):
    conn.config = {"events_etag": 'W/"old"'}
    conn.save()
    api.add(
        "GET",
        EVENTS_URL,
        json=[push_event(11), release_event(12), release_event(13, action="created"), {"id": "14", "type": "WatchEvent", "repo": {"name": "x/y"}, "payload": {}, "created_at": "2026-11-10T10:00:00Z"}],
        headers={"ETag": 'W/"new"'},
    )

    github.poll_events(conn)

    push = Event.objects.get(type="github.push")
    assert push.external_id == "gh-11"
    assert push.source == "github"
    assert push.public is True
    assert push.payload == {
        "repo": "A1isherDev/atlas",
        "branch": "main",
        "commits": 2,
        "url": "https://github.com/A1isherDev/atlas/compare/000111...abc123",
        "head": "abc123",
    }
    assert push.occurred_at.isoformat() == "2026-11-10T10:00:00+00:00"
    assert push.dispatched_at is None
    release = Event.objects.get(type="github.release.published")
    assert release.external_id == "gh-12"
    assert release.payload == {"repo": "A1isherDev/atlas", "tag": "v1.2.0", "name": "Spring", "url": "https://github.com/A1isherDev/atlas/releases/tag/v1.2.0"}
    assert Event.objects.count() == 2
    assert api.requests[0].headers["If-None-Match"] == 'W/"old"'
    conn.refresh_from_db()
    assert conn.config["events_etag"] == 'W/"new"'


def test_not_modified_events_emit_nothing(api, conn):
    conn.config = {"events_etag": 'W/"same"'}
    conn.save()
    api.add("GET", EVENTS_URL, status=304)
    github.poll_events(conn)
    assert not Event.objects.exists()


def test_first_poll_backfills_without_triggering_rules(api, conn):
    api.add("GET", EVENTS_URL, json=[push_event(21)], headers={"ETag": '"e1"'})
    github.poll_events(conn)
    assert Event.objects.get().dispatched_at is not None


def test_events_already_seen_are_not_duplicated(api, conn):
    conn.config = {"events_etag": "x"}
    conn.save()
    api.add("GET", EVENTS_URL, json=[push_event(31)])
    github.poll_events(conn)
    github.poll_events(conn)
    assert Event.objects.count() == 1


def test_push_already_received_by_webhook_is_not_repeated(api, conn):
    conn.config = {"events_etag": "x"}
    conn.save()
    Event.objects.create(type="github.push", external_id="ghd-xyz", payload={"repo": "A1isherDev/atlas", "head": "abc123"})
    api.add("GET", EVENTS_URL, json=[push_event(41, head="abc123")])
    github.poll_events(conn)
    assert Event.objects.count() == 1


def test_tag_pushes_are_ignored(api, conn):
    conn.config = {"events_etag": "x"}
    conn.save()
    api.add("GET", EVENTS_URL, json=[push_event(51, ref="refs/tags/v1")])
    github.poll_events(conn)
    assert not Event.objects.exists()


def test_events_poll_with_a_rejected_token_is_an_auth_error(api, conn):
    api.add("GET", EVENTS_URL, status=401, json={})
    with pytest.raises(AuthError):
        github.poll_events(conn)


def test_missing_commit_count_is_left_out(api, conn):
    conn.config = {"events_etag": "x"}
    conn.save()
    event = push_event(61)
    del event["payload"]["size"]
    api.add("GET", EVENTS_URL, json=[event])
    github.poll_events(conn)
    assert Event.objects.get().payload["commits"] is None


def test_timeouts_are_transient(api, conn):
    api.add("GET", EVENTS_URL, httpx.ConnectTimeout("slow"))
    with pytest.raises(Transient):
        github.poll_events(conn)
