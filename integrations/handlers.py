"""Job handlers for provider work. Registered on app start (IntegrationsConfig.ready).

A job for a provider that was disconnected after the job was queued does nothing.
"""
from automations.models import Event
from jobs.registry import handler

from .health import record_success
from .models import Connection, OutboundHook
from .providers import github, lastfm, telegram, webhook

SECRET_KEYS = {"github": "token", "lastfm": "api_key", "telegram": "bot_token"}


def live_connection(provider):
    """The provider's connection if it has credentials and is not switched off, else None."""
    conn = Connection.objects.filter(provider=provider).exclude(status=Connection.Status.OFF).first()
    if conn and conn.credentials.get(SECRET_KEYS[provider]):
        return conn
    return None


@handler("github.sync")
def github_sync(payload):
    conn = live_connection("github")
    if conn:
        github.full_sync(conn)


@handler("github.events")
def github_events(payload):
    conn = live_connection("github")
    if conn:
        github.poll_events(conn)


@handler("lastfm.poll")
def lastfm_poll(payload):
    conn = live_connection("lastfm")
    if conn:
        lastfm.poll(conn)


@handler("telegram.sync")
def telegram_sync(payload):
    """Re-check the bot token and pick up the owner's chat if it is still missing."""
    conn = live_connection("telegram")
    if not conn:
        return
    token = conn.credentials["bot_token"]
    me = telegram.verify(token)
    config = dict(conn.config or {})
    if not config.get("chat_id"):
        chat_id = telegram.find_chat_id(token)
        if chat_id:
            config["chat_id"] = chat_id
    Connection.objects.filter(pk=conn.pk).update(account=f"@{me['username']}", config=config)
    record_success(conn)


@handler("webhook.deliver")
def webhook_deliver(payload):
    hook = OutboundHook.objects.filter(pk=payload.get("hook_id"), is_active=True).first()
    event = Event.objects.filter(pk=payload.get("event_id")).first()
    if hook and event:
        webhook.deliver(hook, event)
