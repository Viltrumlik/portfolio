"""Turn models into the plain dicts the studio templates render (IntegrationCard, AutomationRule, ActivityFeed rows)."""
from django.urls import reverse
from django.utils import timezone

from automations.models import Rule, RuleRun
from content.models import Profile
from integrations.models import OutboundHook, SyncRun
from integrations.services import connection_summary
from jobs.models import Job
from web import live

from .catalog import ACTIONS, CODE_NAMES, EVENT_INFO, PROVIDERS, SOURCE_CODES, TRIGGER_SLUGS

BADGES = {
    "off": {"label": "Not connected", "tone": "neutral"},
    "syncing": {"label": "Syncing", "tone": "accent", "dot": True, "pulse": True},
    "connected": {"label": "Connected", "tone": "live", "dot": True},
    "error": {"label": "Needs attention", "tone": "danger", "icon": "alert"},
}


# --- connections ----------------------------------------------------------------------


def integration_card(item):
    """One IntegrationCard from a connection_summary() entry."""
    provider, status = item["provider"], item["status"]
    meta = PROVIDERS[provider]
    last = live.relative(item["last_synced_at"]) or "Not synced yet"
    facts = [
        ("Account", item["account"]),
        ("Last sync", f"{last} · {meta['cadence']}"),
        ("Access", ", ".join(item["scopes"])),
        (meta["secret_label"], item["secret"]),
    ]
    if provider == "github":
        facts.append(("Webhook secret", "Saved" if item.get("webhook_secret_set") else "Not set"))
    elif provider == "telegram":
        facts.append(("Channel", item.get("channel_id")))
        facts.append(("Chat", "Verified" if item.get("chat_verified") else "Not verified yet"))
    elif provider == "lastfm":
        facts.append(("Username", item.get("username")))
    return {
        **item,
        "description": meta["feeds"],
        "cls": f"at-integ is-{status}",
        "badge": BADGES[status],
        "facts": [(k, v) for k, v in facts if v],
        "url": reverse("studio:connection", args=[provider]),
        "sync_url": reverse("studio:sync", args=[provider]),
        "disconnect_url": reverse("studio:disconnect", args=[provider]),
    }


def integration_cards():
    return [integration_card(item) for item in connection_summary().values()]


def dock_items(cards):
    """One dock item per connected service (and WH when an outgoing webhook is on)."""
    items = [{"code": c["code"], "label": c["name"], "href": c["url"]} for c in cards if c["status"] != "off"]
    if OutboundHook.objects.filter(is_active=True).exists():
        items.append({"code": "WH", "label": "Outgoing webhooks", "href": reverse("studio:webhooks")})
    return items


# --- sync log -------------------------------------------------------------------------


def feed_time(when, tzname=None, now=None):
    """(time, datetime) for an ActivityFeed row: "14:02" today, "Mar 4" before, in the owner's zone."""
    tz = live.zone(tzname or Profile.load().timezone)
    local = when.astimezone(tz)
    today = (now or timezone.now()).astimezone(tz).date()
    return (f"{local:%H:%M}" if local.date() == today else f"{local:%b} {local.day}"), when.isoformat()


def _row(when, code, text, meta="", tone=None, tz=None):
    time, iso = feed_time(when, tz)
    return {"when": when, "time": time, "datetime": iso, "code": code, "source": CODE_NAMES.get(code, code),
            "text": text, "meta": meta, "tone": tone}


def _code_for_kind(kind):
    return SOURCE_CODES.get(kind.split(".", 1)[0], "ST")


def sync_log(limit=10):
    """Recent sync runs, failed jobs and rule runs, newest first, as ActivityFeed rows."""
    tz = Profile.load().timezone
    rows = []
    for run in SyncRun.objects.select_related("connection").order_by("-started_at")[:limit]:
        provider = run.connection.provider
        name = PROVIDERS.get(provider, {}).get("name", provider)
        code = SOURCE_CODES.get(provider, "ST")
        when = run.finished_at or run.started_at
        if run.status == SyncRun.Status.FAILED:
            rows.append(_row(when, code, f"{name} sync failed", run.message, "danger", tz))
        elif run.status == SyncRun.Status.RUNNING:
            rows.append(_row(when, code, f"Syncing {name}", run.kind, tz=tz))
        else:
            rows.append(_row(when, code, f"Synced {name}", f"{run.items_changed} changed", tz=tz))
    for job in Job.objects.filter(status=Job.Status.FAILED).order_by("-finished_at", "-id")[:limit]:
        rows.append(_row(job.finished_at or job.run_at, _code_for_kind(job.kind), f"{job.kind} failed", job.last_error, "danger", tz))
    verbs = {RuleRun.Status.OK: "ran", RuleRun.Status.FAILED: "failed", RuleRun.Status.SKIPPED: "skipped"}
    for run in RuleRun.objects.select_related("rule").order_by("-ran_at")[:limit]:
        code = ACTIONS.get(run.rule.action, {}).get("code", "ST")
        tone = "danger" if run.status == RuleRun.Status.FAILED else None
        rows.append(_row(run.ran_at, code, f"“{run.rule.name}” {verbs.get(run.status, run.status)}", run.output, tone, tz))
    rows.sort(key=lambda r: r["when"], reverse=True)
    return rows[:limit]


def rule_runs(rule, limit=10):
    tz = Profile.load().timezone
    verbs = {RuleRun.Status.OK: "Ran", RuleRun.Status.FAILED: "Failed", RuleRun.Status.SKIPPED: "Skipped"}
    code = ACTIONS.get(rule.action, {}).get("code", "ST")
    return [
        _row(run.ran_at, code, f"{verbs.get(run.status, run.status)} on {run.event.type}", run.output,
             "danger" if run.status == RuleRun.Status.FAILED else None, tz)
        for run in rule.runs.select_related("event").order_by("-ran_at")[:limit]
    ]


# --- automation rules -----------------------------------------------------------------


def _filter_detail(filters):
    parts = []
    repos = (filters or {}).get("repo")
    if repos:
        parts.append("repo " + ", ".join(repos if isinstance(repos, list) else [repos]))
    if (filters or {}).get("branch"):
        parts.append(f"branch {filters['branch']}")
    return " · ".join(parts)


def _action_detail(rule, hooks, telegram):
    if rule.action == Rule.Action.TELEGRAM_SEND:
        return f"to my chat via {telegram.account}" if telegram and telegram.account else "to my chat"
    if rule.action == Rule.Action.TELEGRAM_POST:
        channel = (telegram.config or {}).get("channel_id") if telegram else ""
        return channel or "no channel set"
    if rule.action == Rule.Action.WEBHOOK_SEND:
        hook = hooks.get((rule.action_config or {}).get("hook_id"))
        return f"{hook.name} · signed POST · HMAC-SHA256" if hook else "no webhook picked"
    if rule.action == Rule.Action.RESYNC:
        return "full GitHub sync"
    return ""


def rule_card(rule, hooks=None, telegram=None):
    trigger = EVENT_INFO.get(rule.trigger, {"label": rule.trigger, "code": "ST", "service": "This site"})
    action = ACTIONS.get(rule.action, {"label": rule.action, "code": "ST", "service": "This site", "slug": rule.action})
    detail = _filter_detail(rule.filters)
    if not detail:
        detail = "any repo" if rule.trigger.startswith("github.") else "every time"
    stats = []
    if rule.run_count is not None:
        stats.append(f"{rule.run_count} run" + ("" if rule.run_count == 1 else "s"))
    if rule.last_run_at:
        stats.append(f"last {live.relative(rule.last_run_at)}")
    slug = TRIGGER_SLUGS.get(rule.trigger, rule.trigger.replace(".", "-"))
    return {
        "rule": rule,
        "title": f"rules/{slug}-to-{action['slug']}",
        "trigger": {**trigger, "detail": detail},
        "action": {**action, "detail": _action_detail(rule, hooks or {}, telegram)},
        "stats": " · ".join(stats),
    }
