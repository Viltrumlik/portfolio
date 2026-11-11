"""Run the rules that match an event. Handler for the `automations.dispatch` job (queued by emit)."""
import logging
import re

from django.db.models import F
from django.utils import timezone

from integrations.errors import AuthError, IntegrationError, Permanent
from integrations.health import record_failure
from integrations.models import Connection, OutboundHook
from integrations.providers import telegram
from jobs.queue import enqueue
from jobs.registry import handler

from .models import Event, Rule, RuleRun

log = logging.getLogger("atlas.automations")

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*)\s*\}\}")


class Skip(Exception):
    """The action cannot apply right now (e.g. its service is not connected). Not a failure."""


# --- templates and filters ------------------------------------------------------------


def _lookup(payload, path):
    value = payload
    for key in path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit() and int(key) < len(value):
            value = value[int(key)]
        else:
            return None
    return value


def render_template(template, payload, *, escape=None):
    """Replace {{key}} and {{a.b}} with payload values. Missing values become "". Nothing else is evaluated."""

    def substitute(match):
        value = _lookup(payload or {}, match.group(1))
        if value is None or isinstance(value, (dict, list)):
            value = ""
        value = str(value)
        return escape(value) if escape else value

    return PLACEHOLDER.sub(substitute, template or "")


def _as_list(value):
    return value if isinstance(value, (list, tuple)) else [value]


def matches(filters, payload):
    """True when every filter matches. `repo` takes names or full names; other keys compare equal."""
    payload = payload or {}
    for key, wanted in (filters or {}).items():
        if wanted in (None, "", []):
            continue
        actual = payload.get(key)
        if actual is None:
            return False
        if key == "repo":
            full = str(actual).lower()
            short = full.rsplit("/", 1)[-1]
            if not any(str(w).lower() in (full, short) for w in _as_list(wanted)):
                return False
        elif actual not in _as_list(wanted):
            return False
    return True


# --- actions --------------------------------------------------------------------------


def _telegram():
    conn = Connection.objects.filter(provider="telegram").exclude(status=Connection.Status.OFF).first()
    if not conn or not conn.credentials.get("bot_token"):
        raise Skip("Telegram is not connected.")
    return conn


def _telegram_text(rule, event):
    return render_template(telegram.template_markup(rule.action_config.get("template", "")), event.payload, escape=telegram.escape_html)


def telegram_send(rule, event):
    conn = _telegram()
    telegram.send_message(conn, _telegram_text(rule, event))
    return "Sent a Telegram message."


def telegram_post_channel(rule, event):
    conn = _telegram()
    telegram.post_channel(conn, _telegram_text(rule, event))
    return f"Posted to {conn.config.get('channel_id', 'the channel')}."


def webhook_send(rule, event):
    hook_id = rule.action_config.get("hook_id")
    hook = OutboundHook.objects.filter(pk=hook_id).first() if hook_id else None
    if hook is None:
        raise Permanent("The rule's webhook no longer exists. Pick a webhook for this rule.", code="no_hook")
    if not hook.is_active:
        raise Skip(f"Webhook “{hook.name}” is paused.")
    enqueue("webhook.deliver", {"hook_id": hook.pk, "event_id": event.pk}, dedupe_key=f"webhook.deliver:{hook.pk}:{event.pk}")
    return f"Queued a signed POST to “{hook.name}”."


def resync_projects(rule, event):
    if not Connection.objects.filter(provider="github").exclude(status=Connection.Status.OFF).exists():
        raise Skip("GitHub is not connected.")
    enqueue("github.sync", {"trigger": event.type, "event_id": event.pk}, dedupe_key="github.sync")
    return "Queued a GitHub sync."


ACTIONS = {
    Rule.Action.TELEGRAM_SEND: telegram_send,
    Rule.Action.TELEGRAM_POST: telegram_post_channel,
    Rule.Action.WEBHOOK_SEND: webhook_send,
    Rule.Action.RESYNC: resync_projects,
}


# --- dispatch -------------------------------------------------------------------------


def run_rule(rule, event):
    """Run one rule's action for `event` and record a RuleRun. Never raises."""
    action = ACTIONS.get(rule.action)
    try:
        if action is None:
            raise Permanent(f"Unknown action {rule.action}.", code="action")
        status, output = RuleRun.Status.OK, action(rule, event)
    except Skip as exc:
        status, output = RuleRun.Status.SKIPPED, str(exc)
    except IntegrationError as exc:
        status, output = RuleRun.Status.FAILED, str(exc)
        if rule.action.startswith("telegram.") and isinstance(exc, (AuthError, Permanent)):
            record_failure("telegram", exc, notify=event.type != "sync.failed")
    except Exception as exc:
        log.exception("rule %s failed on event %s", rule.pk, event.pk)
        status, output = RuleRun.Status.FAILED, f"{exc.__class__.__name__}: {exc}"
    run = RuleRun.objects.create(rule=rule, event=event, status=status, output=output)
    if status != RuleRun.Status.SKIPPED:
        Rule.objects.filter(pk=rule.pk).update(run_count=F("run_count") + 1, last_run_at=timezone.now())
    return run


@handler("automations.dispatch")
def dispatch(payload):
    """Run every enabled rule whose trigger and filters match, and queue deliveries to subscribed hooks."""
    event = Event.objects.filter(pk=(payload or {}).get("event_id")).first()
    if event is None:
        return
    # Claim the event first: a retried or duplicate dispatch must not send anything twice.
    if not Event.objects.filter(pk=event.pk, dispatched_at__isnull=True).update(dispatched_at=timezone.now()):
        return
    for rule in Rule.objects.filter(is_enabled=True, trigger=event.type).order_by("pk"):
        if matches(rule.filters, event.payload):
            run_rule(rule, event)
    for hook in OutboundHook.objects.filter(is_active=True).order_by("pk"):
        if event.type in (hook.events or []):
            enqueue("webhook.deliver", {"hook_id": hook.pk, "event_id": event.pk}, dedupe_key=f"webhook.deliver:{hook.pk}:{event.pk}")
