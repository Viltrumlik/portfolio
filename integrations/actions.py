"""Owner actions: the only entry points the studio uses to connect, disconnect and sync services.

Every function verifies before saving and raises a typed error (integrations.errors) whose message
is a sentence safe to show the owner.
"""
import re
from contextlib import contextmanager

from django.db import transaction

from jobs.models import Job
from jobs.queue import enqueue

from .errors import AuthError, Permanent, RateLimited, Transient
from .models import Connection, OutboundHook
from .providers import github, lastfm, telegram, webhook

NAMES = dict(Connection.Provider.choices)
SYNC_KIND = {"github": "github.sync", "lastfm": "lastfm.poll", "telegram": "telegram.sync"}
SECRET_KEY = {"github": "token", "lastfm": "api_key", "telegram": "bot_token"}


@contextmanager
def _while_connecting(service):
    """A service outage during connect should say 'try again', not 'it will retry'."""
    try:
        yield
    except RateLimited as exc:
        raise RateLimited(exc.retry_after_seconds, f"{service} is rate limiting us. Try again in a few minutes.", code=exc.code) from exc
    except Transient as exc:
        raise Transient(f"{service} could not be reached. Try again in a minute.", code=exc.code) from exc


def _connection(provider):
    if provider not in NAMES:
        raise Permanent(f"Unknown service: {provider}.", code="provider")
    conn, _ = Connection.objects.get_or_create(provider=provider)
    return conn


def _require(provider):
    conn = _connection(provider)
    if conn.status == Connection.Status.OFF or not conn.credentials.get(SECRET_KEY[provider]):
        raise Permanent(f"Connect {NAMES[provider]} first.", code="not_connected")
    return conn


def _save(conn, *, status, account, credentials, config, scopes=()):
    conn.status = status
    conn.account = account
    conn.credentials = credentials
    conn.config = config
    conn.scopes = list(scopes)
    conn.last_error = ""
    conn.error_code = ""
    conn.save()
    return conn


# --- connect --------------------------------------------------------------------------


def connect_github(token, webhook_secret=""):
    """Verify a GitHub token, save it (with an optional webhook secret) and queue a full sync."""
    token = (token or "").strip()
    if not token:
        raise AuthError("Paste a GitHub token to connect.", code="empty")
    with _while_connecting("GitHub"):
        info = github.verify(token)
    with transaction.atomic():
        conn = _connection("github")
        secret = (webhook_secret or "").strip() or conn.credentials.get("webhook_secret", "")
        credentials = {"token": token, **({"webhook_secret": secret} if secret else {})}
        config = dict(conn.config or {}) if conn.account == info["login"] else {}
        conn.next_sync_at = None
        _save(conn, status=Connection.Status.SYNCING, account=info["login"], credentials=credentials, config=config, scopes=info["scopes"])
        enqueue("github.sync", dedupe_key="github.sync")
        enqueue("github.events", dedupe_key="github.events")
    return conn


def _channel(channel_id):
    channel_id = (channel_id or "").strip()
    link = re.match(r"^(?:https?://)?t\.me/([A-Za-z0-9_]{4,})/?$", channel_id)
    if link:
        return "@" + link.group(1)
    return channel_id


def connect_telegram(bot_token, channel_id=""):
    """Verify a bot token, save it with an optional channel, and pick up the owner's chat if /start was sent."""
    bot_token = (bot_token or "").strip()
    if not bot_token:
        raise AuthError("Paste the bot token from @BotFather to connect.", code="empty")
    with _while_connecting("Telegram"):
        me = telegram.verify(bot_token)
        try:
            chat_id = telegram.find_chat_id(bot_token)
        except (Permanent, Transient, RateLimited):
            chat_id = None  # best effort; verify_telegram_chat() can find it later
    with transaction.atomic():
        conn = _connection("telegram")
        account = f"@{me['username']}"
        config = {"channel_id": _channel(channel_id)}
        previous_chat = (conn.config or {}).get("chat_id") if conn.account == account else None
        if chat_id or previous_chat:
            config["chat_id"] = chat_id or previous_chat
        _save(conn, status=Connection.Status.CONNECTED, account=account, credentials={"bot_token": bot_token}, config=config)
        enqueue("telegram.sync", dedupe_key="telegram.sync")
    return conn


def verify_telegram_chat():
    """Find the private chat that sent /start to the bot, save it, and send a confirmation there."""
    conn = _require("telegram")
    with _while_connecting("Telegram"):
        chat_id = telegram.find_chat_id(conn.credentials["bot_token"])
    if not chat_id:
        raise Permanent(f"No /start message yet. Open {conn.account or 'the bot'} in Telegram, send /start, then verify again.", code="no_chat")
    conn.config = {**(conn.config or {}), "chat_id": chat_id}
    conn.save(update_fields=["config", "updated_at"])
    with _while_connecting("Telegram"):
        telegram.send_message(conn, "Connected. Contact-form messages and sync alerts will arrive here.")
    return conn


def connect_lastfm(username, api_key):
    """Verify a Last.fm user and API key, save them, and queue a first poll."""
    username, api_key = (username or "").strip(), (api_key or "").strip()
    if not username or not api_key:
        raise AuthError("Enter the Last.fm username and API key to connect.", code="empty")
    with _while_connecting("Last.fm"):
        user = lastfm.verify(username, api_key)
    with transaction.atomic():
        conn = _connection("lastfm")
        _save(conn, status=Connection.Status.SYNCING, account=user["name"], credentials={"api_key": api_key}, config={"username": user["name"]})
        enqueue("lastfm.poll", dedupe_key="lastfm.poll")
    return conn


# --- manage ---------------------------------------------------------------------------


def disconnect(provider):
    """Forget the credentials and stop syncing. Cached repos, contributions and tracks stay."""
    with transaction.atomic():
        conn = _connection(provider)
        conn.next_sync_at = None
        _save(conn, status=Connection.Status.OFF, account="", credentials={}, config={})
        Job.objects.filter(kind__startswith=f"{provider}.", status=Job.Status.QUEUED).delete()
    return conn


def request_sync(provider):
    """Queue the provider's sync now ("Sync now"). Returns the queued Job."""
    conn = _require(provider)
    with transaction.atomic():
        Connection.objects.filter(pk=conn.pk).update(status=Connection.Status.SYNCING)
        job = enqueue(SYNC_KIND[provider], dedupe_key=SYNC_KIND[provider])
        if provider == "github":
            enqueue("github.events", dedupe_key="github.events")
    return job


def send_test(hook):
    """POST a signed ping to an outgoing webhook. Returns the status code; raises on failure."""
    if not isinstance(hook, OutboundHook):
        hook = OutboundHook.objects.get(pk=hook)
    return webhook.send_ping(hook)
