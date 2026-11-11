import pytest

from integrations import actions
from integrations.errors import AuthError, Permanent, Transient
from integrations.models import Connection, OutboundHook, Repo
from integrations.providers import github, lastfm, telegram, webhook
from jobs.models import Job

pytestmark = pytest.mark.django_db

GRAPHQL = "https://api.github.com/graphql"
TG = "https://api.telegram.org/bot1:tok"


def queued():
    return sorted(Job.objects.filter(status="queued").values_list("kind", flat=True))


# --- GitHub ---------------------------------------------------------------------------


def test_connect_github_verifies_saves_and_queues_a_sync(api):
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}}, headers={"X-OAuth-Scopes": "public_repo, read:user"})
    conn = actions.connect_github(" ghp_new ", webhook_secret="whsec")
    conn.refresh_from_db()
    assert conn.status == Connection.Status.SYNCING
    assert conn.account == "A1isherDev"
    assert conn.scopes == ["public_repo", "read:user"]
    assert conn.credentials == {"token": "ghp_new", "webhook_secret": "whsec"}
    assert queued() == ["github.events", "github.sync"]


def test_connect_github_with_a_bad_token_saves_nothing(api):
    api.add("POST", GRAPHQL, status=401, json={})
    with pytest.raises(AuthError, match="GitHub rejected the token"):
        actions.connect_github("bad")
    assert not Connection.objects.filter(status="syncing").exists()
    assert queued() == []


def test_connect_github_requires_a_token():
    with pytest.raises(AuthError, match="token"):
        actions.connect_github("  ")


def test_reconnecting_keeps_the_webhook_secret_when_none_is_given(api):
    Connection.objects.create(provider="github", status="error", account="A1isherDev", credentials={"token": "old", "webhook_secret": "keep"}, config={"events_etag": "e"})
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}})
    conn = actions.connect_github("new")
    assert conn.credentials == {"token": "new", "webhook_secret": "keep"}
    assert conn.config == {"events_etag": "e"}
    assert conn.last_error == ""


def test_connect_github_when_github_is_down_says_to_try_again(api):
    api.add("POST", GRAPHQL, status=503, json={})
    with pytest.raises(Transient, match="Try again"):
        actions.connect_github("t")


# --- Telegram -------------------------------------------------------------------------


def test_connect_telegram_verifies_and_finds_the_chat(api):
    api.add("GET", f"{TG}/getMe", json={"ok": True, "result": {"id": 1, "username": "atlas_bot"}})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": [{"message": {"chat": {"id": 77, "type": "private"}, "text": "/start"}}]})
    conn = actions.connect_telegram("1:tok", channel_id="https://t.me/atlas_news")
    conn.refresh_from_db()
    assert conn.status == Connection.Status.CONNECTED
    assert conn.account == "@atlas_bot"
    assert conn.credentials == {"bot_token": "1:tok"}
    assert conn.config == {"channel_id": "@atlas_news", "chat_id": 77}
    assert queued() == ["telegram.sync"]


def test_connect_telegram_with_a_bad_token(api):
    api.add("GET", f"{TG}/getMe", status=401, json={"ok": False, "error_code": 401, "description": "Unauthorized"})
    with pytest.raises(AuthError, match="Telegram rejected the bot token"):
        actions.connect_telegram("1:tok")


def test_verify_telegram_chat_saves_the_chat_and_says_hello(api):
    Connection.objects.create(provider="telegram", status="connected", credentials={"bot_token": "1:tok"}, config={})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": [{"message": {"chat": {"id": 88, "type": "private"}, "text": "/start"}}]})
    api.add("POST", f"{TG}/sendMessage", json={"ok": True, "result": {}})
    conn = actions.verify_telegram_chat()
    assert conn.config["chat_id"] == 88
    assert len(api.calls("POST", "sendMessage")) == 1


def test_verify_telegram_chat_without_a_start_explains_what_to_do(api):
    Connection.objects.create(provider="telegram", status="connected", credentials={"bot_token": "1:tok"})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": []})
    with pytest.raises(Permanent, match="/start"):
        actions.verify_telegram_chat()


def test_verify_telegram_chat_requires_a_connection():
    with pytest.raises(Permanent, match="Connect Telegram"):
        actions.verify_telegram_chat()


# --- Last.fm --------------------------------------------------------------------------


def test_connect_lastfm_verifies_and_queues_a_poll(api):
    api.add("GET", "https://ws.audioscrobbler.com/2.0/", json={"user": {"name": "Alisher", "url": "u"}})
    conn = actions.connect_lastfm("alisher", "key123")
    conn.refresh_from_db()
    assert conn.account == "Alisher"
    assert conn.credentials == {"api_key": "key123"}
    assert conn.config == {"username": "Alisher"}
    assert queued() == ["lastfm.poll"]


def test_connect_lastfm_with_a_bad_key(api):
    api.add("GET", "https://ws.audioscrobbler.com/2.0/", status=403, json={"error": 10, "message": "Invalid API key"})
    with pytest.raises(AuthError, match="Last.fm rejected the API key"):
        actions.connect_lastfm("alisher", "bad")


# --- disconnect / sync / test ---------------------------------------------------------


def test_disconnect_clears_credentials_but_keeps_cached_data():
    Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "t"}, scopes=["repo"])
    Repo.objects.create(github_id=1, name="a", full_name="A1isherDev/a", url="https://github.com/A1isherDev/a")
    Job.objects.create(kind="github.sync")
    Job.objects.create(kind="lastfm.poll")
    conn = actions.disconnect("github")
    conn.refresh_from_db()
    assert (conn.status, conn.credentials, conn.account, conn.scopes) == ("off", {}, "", [])
    assert Repo.objects.count() == 1
    assert queued() == ["lastfm.poll"]


def test_disconnect_unknown_provider_is_refused():
    with pytest.raises(Permanent):
        actions.disconnect("myspace")


def test_request_sync_queues_the_providers_sync():
    Connection.objects.create(provider="lastfm", status="error", credentials={"api_key": "k"})
    job = actions.request_sync("lastfm")
    assert job.kind == "lastfm.poll"
    assert Connection.objects.get(provider="lastfm").status == Connection.Status.SYNCING


def test_request_sync_for_github_also_polls_events():
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    actions.request_sync("github")
    assert queued() == ["github.events", "github.sync"]


def test_request_sync_requires_a_connection():
    with pytest.raises(Permanent, match="Connect GitHub first"):
        actions.request_sync("github")


def test_send_test_pings_the_hook(api, resolve_to):
    resolve_to("93.184.216.34")
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/h", secret={"secret": "s"})
    api.add("POST", "https://93.184.216.34/h", status=200, json={})
    assert actions.send_test(hook) == 200


def test_actions_are_the_providers_entry_points():
    # The studio imports only integrations.actions; the provider modules stay internal.
    for name in ["connect_github", "connect_telegram", "verify_telegram_chat", "connect_lastfm", "disconnect", "request_sync", "send_test"]:
        assert callable(getattr(actions, name))
    assert github and lastfm and telegram and webhook
