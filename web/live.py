"""Read cached service data for public pages. Visitors never trigger a live call to a service."""
import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from automations.models import Event
from integrations.models import ContributionDay, ListeningSnapshot

LISTENING_MAX_AGE = dt.timedelta(minutes=60)

SOURCE_CODES = {
    "github": "GH", "wakatime": "WK", "lastfm": "LF", "telegram": "TG",
    "webhook": "WH", "rss": "RS", "site": "ST",
}
CODE_NAMES = {"GH": "GitHub", "WK": "WakaTime", "LF": "Last.fm", "TG": "Telegram", "WH": "Webhook", "RS": "RSS", "ST": "This site"}


def zone(name):
    try:
        return ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def local_now(tzname):
    return timezone.now().astimezone(zone(tzname))


def utc_label(tzname):
    offset = local_now(tzname).utcoffset() or dt.timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    if minutes == 0:
        return "UTC"
    sign = "+" if minutes > 0 else "-"
    h, m = divmod(abs(minutes), 60)
    return f"UTC{sign}{h}" + (f":{m:02d}" if m else "")


def relative(when, now=None):
    """"just now", "4 min ago", "3 h ago", "2 days ago", then "Mar 2026"."""
    if not when:
        return ""
    now = now or timezone.now()
    seconds = max(0, (now - when).total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h ago"
    days = int(seconds // 86400)
    if days < 45:
        return "1 day ago" if days == 1 else f"{days} days ago"
    return f"{when:%b %Y}"


# --- now.app ----------------------------------------------------------------------------


def current_listening(now=None):
    """The latest Last.fm snapshot, if it was fetched in the last hour and the track is current."""
    now = now or timezone.now()
    cutoff = now - LISTENING_MAX_AGE
    snap = ListeningSnapshot.objects.filter(fetched_at__gte=cutoff).order_by("-fetched_at").first()
    if snap and (snap.now_playing or snap.played_at is None or snap.played_at >= cutoff):
        return snap
    return None


def listening_payload(snap, now=None):
    if snap is None:
        return None
    return {
        "track": snap.track,
        "artist": snap.artist,
        "album": snap.album,
        "url": snap.url,
        "image_url": snap.image_url,
        "now_playing": snap.now_playing,
        "played_at": snap.played_at.isoformat() if snap.played_at else None,
        "played": "Now playing" if snap.now_playing or not snap.played_at else relative(snap.played_at, now),
    }


def availability(profile):
    """{"status", "label", "tone"}; status "hidden" means don't show it."""
    status = profile.availability
    if status == profile.Availability.HIDDEN:
        return {"status": status, "label": "", "tone": "neutral"}
    label = profile.availability_note or profile.get_availability_display()
    return {"status": status, "label": label, "tone": "live" if status == profile.Availability.AVAILABLE else "neutral"}


# --- github.app -------------------------------------------------------------------------


def graph_label(weeks):
    if weeks == 26:
        return "contributions in the last six months"
    if weeks in (52, 53):
        return "contributions in the last year"
    return f"contributions in the last {weeks} weeks"


def contribution_days(weeks=26):
    """[(date, count)] for the last `weeks` calendar weeks up to the newest synced day, starting on a Sunday."""
    last = ContributionDay.objects.order_by("-date").first()
    if last is None:
        return []
    end = last.date
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=weeks - 1)
    counts = dict(ContributionDay.objects.filter(date__gte=start, date__lte=end).values_list("date", "count"))
    days = []
    day = start
    while day <= end:
        days.append((day, counts.get(day, 0)))
        day += dt.timedelta(days=1)
    return days


# --- activity.log -----------------------------------------------------------------------


def public_events(limit=10):
    return list(Event.objects.filter(public=True).order_by("-occurred_at")[:limit])


def _commit_count(payload):
    commits = payload.get("commits", payload.get("size", payload.get("count")))
    if isinstance(commits, list):
        return len(commits)
    if isinstance(commits, int):
        return commits
    return None


def describe_event(event):
    """(text, meta, tone) for one event, from its type and payload."""
    p = event.payload if isinstance(event.payload, dict) else {}
    repo = p.get("repo") or p.get("repository") or ""
    if isinstance(repo, dict):
        repo = repo.get("full_name") or repo.get("name") or ""
    tone = "danger" if event.type.endswith(".failed") or p.get("tone") == "danger" else None
    text = p.get("text") or p.get("summary")
    meta = p.get("meta")
    if not text:
        if event.type == "github.push":
            n = _commit_count(p)
            text = (f"Pushed {n} commit{'' if n == 1 else 's'} to {repo}" if n else f"Pushed to {repo}").strip()
            meta = meta or p.get("branch")
        elif event.type.startswith("github.release"):
            tag = p.get("tag") or p.get("tag_name") or p.get("name") or ""
            text = f"Released {tag} of {repo}".replace("  ", " ").strip()
        elif event.type == "post.published":
            text = f"Published “{p.get('title', '')}”"
        elif tone == "danger":
            text = f"{event.source or 'Sync'} sync failed".capitalize()
        else:
            text = p.get("title") or event.type.replace(".", " ").replace("_", " ").capitalize()
    return text, meta, tone


def event_item(event, tzname, now=None):
    local = event.occurred_at.astimezone(zone(tzname))
    today = (now or timezone.now()).astimezone(zone(tzname)).date()
    code = SOURCE_CODES.get((event.source or "").lower()) or SOURCE_CODES.get(event.type.split(".")[0], "ST")
    text, meta, tone = describe_event(event)
    return {
        "time": f"{local:%H:%M}" if local.date() == today else f"{local:%b} {local.day}",
        "datetime": event.occurred_at.isoformat(),
        "code": code,
        "source": CODE_NAMES.get(code, code),
        "text": text,
        "meta": meta,
        "tone": tone,
    }
