"""The studio desk and the connect / disconnect / sync flows, with provider HTTP mocked."""
import datetime as dt

import pytest
from django.utils import timezone

from automations.models import Event, Rule, RuleRun
from integrations.models import Connection, SyncRun
from jobs.models import Job

pytestmark = pytest.mark.django_db

GRAPHQL = "https://api.github.com/graphql"
TG = "https://api.telegram.org/bot1:tok"
LASTFM = "https://ws.audioscrobbler.com/2.0/"


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


def queued():
    return sorted(Job.objects.filter(status="queued").values_list("kind", flat=True))


# --- desk -----------------------------------------------------------------------------


def test_desk_shows_one_integration_window_per_provider_with_state_copy(staff):
    Connection.objects.create(provider="github", status="connected", account="A1isherDev", scopes=["public_repo", "read:user"],
                              credentials={"token": "ghp_secret_91ab"}, last_synced_at=timezone.now() - dt.timedelta(minutes=4))
    Connection.objects.create(provider="lastfm", status="error", account="Alisher", credentials={"api_key": "k"},
                              last_error="Last.fm rejected the API key (error 10). Paste a new key to resume syncing.", error_code="lastfm-10")
    page = html(staff.get("/studio/"))
    assert 'data-island="desk"' in page
    # GitHub: connected
    assert 'at-integ is-connected"' in page
    assert '<span class="at-win__title">connections/github</span>' in page
    assert '<span class="at-badge at-badge--live"><span class="at-badge__dot" aria-hidden="true"></span>Connected</span>' in page
    assert "A1isherDev" in page and "public_repo, read:user" in page
    assert "4 min ago · hourly + push" in page
    assert "Sync now" in page
    assert "ghp_secret_91ab" not in page and "•••• 91ab" in page
    # Last.fm: error
    assert 'class="at-win at-integ is-error"' in page
    assert "Needs attention" in page and "Last.fm rejected the API key (error 10)" in page and "lastfm-10" in page
    assert "Reconnect" in page
    # Telegram: off
    assert 'class="at-win at-integ is-off"' in page
    assert "Not connected" in page and ">Connect<" in page
    assert "Forwards contact-form messages" in page


def test_desk_syncing_card_has_a_disabled_button(staff):
    Connection.objects.create(provider="github", status="syncing", account="A1isherDev", credentials={"token": "t"})
    page = html(staff.get("/studio/"))
    assert 'at-integ is-syncing"' in page
    assert '<span class="at-badge__dot is-pulse" aria-hidden="true"></span>Syncing</span>' in page
    assert "disabled><svg" in page and "Syncing…" in page


def test_desk_dock_lists_only_connected_services(staff):
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    page = html(staff.get("/studio/"))
    assert '<nav class="at-dock" aria-label="Connected services">' in page
    assert 'href="/studio/connections/github/" class="at-dock__item"' in page
    assert 'href="/studio/connections/lastfm/" class="at-dock__item"' not in page


def test_desk_sync_log_shows_runs_failed_jobs_and_rule_runs(staff):
    conn = Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    SyncRun.objects.create(connection=conn, kind="github.sync", status="ok", items_changed=12, finished_at=timezone.now())
    Job.objects.create(kind="lastfm.poll", status="failed", last_error="Last.fm could not be reached.", finished_at=timezone.now())
    rule = Rule.objects.get(trigger="contact.submitted", action="telegram.send")
    RuleRun.objects.create(rule=rule, event=Event.objects.create(type="contact.submitted"), status="failed", output="Telegram is down.")
    page = html(staff.get("/studio/"))
    assert '<span class="at-win__title">activity.log</span>' in page
    assert "Synced GitHub" in page and "12 changed" in page
    assert "lastfm.poll failed" in page and "Last.fm could not be reached." in page
    assert "Forward contact messages to Telegram" in page and "Telegram is down." in page
    assert page.count('class="at-feed__row is-danger"') == 2


# --- connection pages -----------------------------------------------------------------


def test_github_page_shows_the_webhook_url_and_never_the_token(staff):
    Connection.objects.create(provider="github", status="connected", account="A1isherDev",
                              credentials={"token": "ghp_secret_91ab", "webhook_secret": "whsec_zzzz"})
    page = html(staff.get("/studio/connections/github/"))
    assert "https://guts.test/hooks/github/" in page
    assert "ghp_secret_91ab" not in page and "whsec_zzzz" not in page
    assert "•••• 91ab" in page
    assert 'name="token"' in page and 'type="password"' in page and 'value="ghp' not in page


def test_connect_github_success(staff, api):
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}}, headers={"X-OAuth-Scopes": "public_repo"})
    r = staff.post("/studio/connections/github/", {"token": "ghp_new", "webhook_secret": "whsec"})
    assert r.status_code == 302 and r["Location"] == "/studio/connections/github/"
    conn = Connection.objects.get(provider="github")
    assert conn.account == "A1isherDev" and conn.credentials == {"token": "ghp_new", "webhook_secret": "whsec"}
    assert queued() == ["github.events", "github.sync"]
    page = html(staff.get(r["Location"]))
    assert "GitHub connected as A1isherDev" in page


def test_connect_github_rejected_token_shows_the_sentence(staff, api):
    api.add("POST", GRAPHQL, status=401, json={})
    page = html(staff.post("/studio/connections/github/", {"token": "bad"}))
    assert "GitHub rejected the token" in page
    assert 'class="at-note at-note--danger" role="alert"' in page
    assert 'value="bad"' not in page
    assert not Connection.objects.exclude(status="off").exists()


def test_connect_github_without_a_token_asks_for_one(staff):
    page = html(staff.post("/studio/connections/github/", {"token": ""}))
    assert "Paste a GitHub token to connect." in page


def test_replacing_with_an_empty_token_keeps_the_saved_one(staff, api):
    Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "ghp_saved"})
    api.add("POST", GRAPHQL, json={"data": {"viewer": {"login": "A1isherDev"}}}, match=lambda r: r.headers["Authorization"].endswith("ghp_saved"))
    r = staff.post("/studio/connections/github/", {"token": "", "webhook_secret": "whsec_new"})
    assert r.status_code == 302
    assert Connection.objects.get(provider="github").credentials == {"token": "ghp_saved", "webhook_secret": "whsec_new"}


def test_connect_telegram_success(staff, api):
    api.add("GET", f"{TG}/getMe", json={"ok": True, "result": {"id": 1, "username": "atlas_bot"}})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": []})
    r = staff.post("/studio/connections/telegram/", {"bot_token": "1:tok", "channel_id": "@atlas_news"})
    assert r.status_code == 302
    conn = Connection.objects.get(provider="telegram")
    assert conn.account == "@atlas_bot" and conn.config == {"channel_id": "@atlas_news"}
    page = html(staff.get("/studio/connections/telegram/"))
    assert "Telegram connected as @atlas_bot" in page
    assert "Verify chat" in page and 'value="@atlas_news"' in page and "1:tok" not in page


def test_connect_telegram_bad_token(staff, api):
    api.add("GET", f"{TG}/getMe", status=401, json={"ok": False, "error_code": 401, "description": "Unauthorized"})
    page = html(staff.post("/studio/connections/telegram/", {"bot_token": "1:tok"}))
    assert "Telegram rejected the bot token" in page


def test_verify_telegram_chat(staff, api):
    Connection.objects.create(provider="telegram", status="connected", account="@atlas_bot", credentials={"bot_token": "1:tok"}, config={})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": [{"message": {"chat": {"id": 88, "type": "private"}, "text": "/start"}}]})
    api.add("POST", f"{TG}/sendMessage", json={"ok": True, "result": {}})
    r = staff.post("/studio/connections/telegram/verify/")
    assert r.status_code == 302 and r["Location"] == "/studio/connections/telegram/"
    assert Connection.objects.get(provider="telegram").config["chat_id"] == 88
    assert "Chat verified" in html(staff.get(r["Location"]))


def test_verify_telegram_chat_without_start_explains(staff, api):
    Connection.objects.create(provider="telegram", status="connected", account="@atlas_bot", credentials={"bot_token": "1:tok"})
    api.add("GET", f"{TG}/getUpdates", json={"ok": True, "result": []})
    page = html(staff.post("/studio/connections/telegram/verify/", follow=True))
    assert "No /start message yet" in page


def test_connect_lastfm_success(staff, api):
    api.add("GET", LASTFM, json={"user": {"name": "Alisher", "url": "u"}})
    r = staff.post("/studio/connections/lastfm/", {"username": "alisher", "api_key": "key123"})
    assert r.status_code == 302
    conn = Connection.objects.get(provider="lastfm")
    assert conn.account == "Alisher" and conn.credentials == {"api_key": "key123"}
    assert queued() == ["lastfm.poll"]


def test_connect_lastfm_bad_key(staff, api):
    api.add("GET", LASTFM, status=403, json={"error": 10, "message": "Invalid API key"})
    page = html(staff.post("/studio/connections/lastfm/", {"username": "alisher", "api_key": "bad"}))
    assert "Last.fm rejected the API key" in page
    assert 'value="alisher"' in page


def test_disconnect_asks_once_then_disconnects_on_post(staff):
    Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "t"})
    page = html(staff.get("/studio/connections/github/disconnect/"))
    assert "Disconnect GitHub? Projects stay on the site but stop updating." in page
    assert Connection.objects.get(provider="github").status == "connected"
    r = staff.post("/studio/connections/github/disconnect/")
    assert r.status_code == 302 and r["Location"] == "/studio/"
    conn = Connection.objects.get(provider="github")
    assert (conn.status, conn.credentials) == ("off", {})
    assert "GitHub disconnected" in html(staff.get("/studio/"))


def test_sync_now_queues_the_sync(staff):
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})
    r = staff.post("/studio/connections/lastfm/sync/")
    assert r.status_code == 302 and r["Location"] == "/studio/connections/lastfm/"
    assert queued() == ["lastfm.poll"]
    assert Connection.objects.get(provider="lastfm").status == "syncing"


def test_sync_now_returns_to_a_safe_next(staff):
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})
    assert staff.post("/studio/connections/lastfm/sync/", {"next": "/studio/"})["Location"] == "/studio/"
    assert staff.post("/studio/connections/lastfm/sync/", {"next": "https://evil.example/"})["Location"] == "/studio/connections/lastfm/"


def test_sync_now_when_not_connected_says_connect_first(staff):
    page = html(staff.post("/studio/connections/github/sync/", follow=True))
    assert "Connect GitHub first." in page
    assert queued() == []
