"""Read helpers for pages and the studio. They only read cached data; nothing here calls a service.

A disconnected service's helpers return empty values ([] or None) so its window can be hidden.
"""
from datetime import timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from automations.models import Event

from .crypto import mask
from .models import Connection, ContributionDay, ListeningSnapshot, Repo

SECRET_KEYS = {"github": "token", "lastfm": "api_key", "telegram": "bot_token"}
SERVICE_CODES = {"github": "GH", "lastfm": "LF", "telegram": "TG", "wakatime": "WK", "webhook": "WH", "site": "ST"}


def _is_on(provider):
    return Connection.objects.filter(provider=provider).exclude(status=Connection.Status.OFF).exists()


def _today(today):
    return today or timezone.now().date()


# --- GitHub -------------------------------------------------------------------------


def contribution_days(weeks=26, today=None):
    """Days for the contribution graph: `weeks` columns (Sunday-first), the last one ending today.

    [{"date": date, "count": int, "level": 0-4}, ...] oldest first; [] when GitHub is not connected.
    """
    if not _is_on("github"):
        return []
    today = _today(today)
    start = today - timedelta(days=(weeks - 1) * 7)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    rows = ContributionDay.objects.filter(date__gte=start, date__lte=today).order_by("date")
    return [{"date": d.date, "count": d.count, "level": d.level} for d in rows]


def contribution_total(days=365, today=None):
    """Contributions in the last `days` days (today included), or None when GitHub is not connected."""
    if not _is_on("github"):
        return None
    today = _today(today)
    total = ContributionDay.objects.filter(date__gt=today - timedelta(days=days), date__lte=today).aggregate(n=Sum("count"))["n"]
    return total or 0


def pinned_repos(limit=6):
    """Pinned repos first, then the most recently pushed own repos (no forks or archives), up to `limit`."""
    if not _is_on("github"):
        return []
    repos = Repo.objects.filter(Q(pinned=True) | Q(is_fork=False, is_archived=False)).order_by("-pinned", "-pushed_at", "id")
    return list(repos[:limit])


# --- Last.fm ------------------------------------------------------------------------


def now_listening(max_age_minutes=60):
    """The track playing now (or played within `max_age_minutes`) as a dict, else None.

    A now-playing track only counts while polling is fresh (last poll within `max_age_minutes`).
    """
    conn = Connection.objects.filter(provider="lastfm").exclude(status=Connection.Status.OFF).first()
    if conn is None:
        return None
    latest = ListeningSnapshot.objects.order_by("-fetched_at", "-id").first()
    if latest is None:
        return None
    cutoff = timezone.now() - timedelta(minutes=max_age_minutes)
    if latest.now_playing:
        if not conn.last_synced_at or conn.last_synced_at < cutoff:
            return None
    elif (latest.played_at or latest.fetched_at) < cutoff:
        return None
    return {
        "track": latest.track,
        "artist": latest.artist,
        "album": latest.album,
        "url": latest.url,
        "image_url": latest.image_url,
        "now_playing": latest.now_playing,
        "played_at": latest.played_at,
    }


# --- activity -----------------------------------------------------------------------


def _describe(event):
    p = event.payload or {}
    if event.type == "github.push":
        commits = p.get("commits")
        branch = f" ({p['branch']})" if p.get("branch") else ""
        if commits:
            noun = "commit" if commits == 1 else "commits"
            return f"Pushed {commits} {noun} to {p.get('repo', '')}{branch}"
        return f"Pushed to {p.get('repo', '')}{branch}"
    if event.type == "github.release.published":
        return f"Released {p.get('tag', '')} of {p.get('repo', '')}"
    if event.type == "post.published":
        return f"Published “{p.get('title', '')}”"
    return event.type


def recent_public_events(limit=10):
    """Public events, newest first: [{"type", "source", "code", "text", "url", "occurred_at", "payload"}]."""
    events = Event.objects.filter(public=True).order_by("-occurred_at", "-id")[:limit]
    return [
        {
            "type": e.type,
            "source": e.source,
            "code": SERVICE_CODES.get(e.source, "ST"),
            "text": _describe(e),
            "url": (e.payload or {}).get("url", ""),
            "occurred_at": e.occurred_at,
            "payload": e.payload,
        }
        for e in events
    ]


# --- studio -------------------------------------------------------------------------


def connection_summary():
    """Per provider: status, labels, account, sync times, last error and a masked secret. Never a full secret."""
    rows = {c.provider: c for c in Connection.objects.all()}
    labels = dict(Connection.Status.choices)
    summary = {}
    for provider, name in Connection.Provider.choices:
        conn = rows.get(provider)
        credentials = conn.credentials if conn else {}
        config = (conn.config if conn else {}) or {}
        status = conn.status if conn else Connection.Status.OFF
        item = {
            "provider": provider,
            "name": name,
            "code": SERVICE_CODES[provider],
            "status": status,
            "status_label": labels[status],
            "account": conn.account if conn else "",
            "scopes": list(conn.scopes) if conn else [],
            "last_synced_at": conn.last_synced_at if conn else None,
            "next_sync_at": conn.next_sync_at if conn else None,
            "last_error": conn.last_error if conn else "",
            "error_code": conn.error_code if conn else "",
            "secret": mask(credentials.get(SECRET_KEYS[provider], "")),
        }
        if provider == "github":
            item["webhook_secret_set"] = bool(credentials.get("webhook_secret"))
        elif provider == "telegram":
            item["channel_id"] = config.get("channel_id", "")
            item["chat_verified"] = bool(config.get("chat_id"))
        elif provider == "lastfm":
            item["username"] = config.get("username", "")
        summary[provider] = item
    return summary
