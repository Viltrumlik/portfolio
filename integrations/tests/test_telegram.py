import pytest

from integrations.errors import AuthError, Permanent, RateLimited, Transient
from integrations.models import Connection
from integrations.providers import telegram
from integrations.tests.fixtures import body_json

pytestmark = pytest.mark.django_db

TOKEN = "123456:ABC-test"
BASE = f"https://api.telegram.org/bot{TOKEN}"


@pytest.fixture
def conn():
    return Connection.objects.create(
        provider="telegram", status="connected", account="@atlas_bot",
        credentials={"bot_token": TOKEN}, config={"chat_id": 555, "channel_id": "@atlas_news"},
    )


def test_escape_html_escapes_markup():
    assert telegram.escape_html('<b>"Tom & Jerry"</b>') == '&lt;b&gt;"Tom &amp; Jerry"&lt;/b&gt;'


def test_verify_returns_the_bot(api):
    api.add("GET", f"{BASE}/getMe", json={"ok": True, "result": {"id": 1, "is_bot": True, "username": "atlas_bot"}})
    assert telegram.verify(TOKEN) == {"id": 1, "username": "atlas_bot"}


def test_verify_with_a_bad_token_is_an_auth_error(api):
    api.add("GET", f"{BASE}/getMe", status=401, json={"ok": False, "error_code": 401, "description": "Unauthorized"})
    with pytest.raises(AuthError, match="Telegram rejected the bot token"):
        telegram.verify(TOKEN)


def test_find_chat_id_returns_the_latest_private_start(api):
    api.add(
        "GET",
        f"{BASE}/getUpdates",
        json={
            "ok": True,
            "result": [
                {"update_id": 1, "message": {"chat": {"id": 111, "type": "private"}, "text": "/start"}},
                {"update_id": 2, "message": {"chat": {"id": -100, "type": "group"}, "text": "/start"}},
                {"update_id": 3, "message": {"chat": {"id": 222, "type": "private"}, "text": "/start hello"}},
                {"update_id": 4, "message": {"chat": {"id": 333, "type": "private"}, "text": "hi"}},
            ],
        },
    )
    assert telegram.find_chat_id(TOKEN) == 222


def test_find_chat_id_without_a_start_returns_none(api):
    api.add("GET", f"{BASE}/getUpdates", json={"ok": True, "result": []})
    assert telegram.find_chat_id(TOKEN) is None


def test_send_message_uses_html_and_the_saved_chat(api, conn):
    api.add("POST", f"{BASE}/sendMessage", json={"ok": True, "result": {"message_id": 9}})
    telegram.send_message(conn, "<b>Hi</b>")
    sent = body_json(api.requests[0])
    assert sent["chat_id"] == 555
    assert sent["text"] == "<b>Hi</b>"
    assert sent["parse_mode"] == "HTML"


def test_send_message_to_an_explicit_chat(api, conn):
    api.add("POST", f"{BASE}/sendMessage", json={"ok": True, "result": {}})
    telegram.send_message(conn, "x", chat_id=777)
    assert body_json(api.requests[0])["chat_id"] == 777


def test_send_message_without_a_chat_is_permanent(conn):
    conn.config = {}
    with pytest.raises(Permanent, match="/start"):
        telegram.send_message(conn, "x")


def test_long_messages_are_cut_to_telegrams_limit(api, conn):
    api.add("POST", f"{BASE}/sendMessage", json={"ok": True, "result": {}})
    telegram.send_message(conn, "a" * 5000 + "&amp;")
    assert len(body_json(api.requests[0])["text"]) <= 4096


def test_post_channel_posts_to_the_configured_channel(api, conn):
    api.add("POST", f"{BASE}/sendMessage", json={"ok": True, "result": {}})
    telegram.post_channel(conn, "New release")
    assert body_json(api.requests[0])["chat_id"] == "@atlas_news"


def test_post_channel_without_a_channel_is_permanent(conn):
    conn.config = {"chat_id": 1}
    with pytest.raises(Permanent, match="channel"):
        telegram.post_channel(conn, "x")


def test_channel_403_says_the_bot_is_not_an_admin(api, conn):
    api.add("POST", f"{BASE}/sendMessage", status=403, json={"ok": False, "error_code": 403, "description": "Forbidden: bot is not a member of the channel chat"})
    with pytest.raises(Permanent, match="bot is not an admin of the channel"):
        telegram.post_channel(conn, "x")


def test_private_403_says_the_bot_was_blocked(api, conn):
    api.add("POST", f"{BASE}/sendMessage", status=403, json={"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"})
    with pytest.raises(Permanent, match="bot was blocked"):
        telegram.send_message(conn, "x")


def test_429_is_rate_limited_with_retry_after(api, conn):
    api.add("POST", f"{BASE}/sendMessage", status=429, json={"ok": False, "error_code": 429, "description": "Too Many Requests", "parameters": {"retry_after": 17}})
    with pytest.raises(RateLimited) as info:
        telegram.send_message(conn, "x")
    assert info.value.retry_after_seconds == 17


def test_bad_request_is_permanent_and_server_errors_transient(api, conn):
    api.add("POST", f"{BASE}/sendMessage", status=400, json={"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}, times=1)
    api.add("POST", f"{BASE}/sendMessage", status=502, json={})
    with pytest.raises(Permanent, match="chat not found"):
        telegram.send_message(conn, "x")
    with pytest.raises(Transient):
        telegram.send_message(conn, "x")


def test_errors_never_include_the_token(api, conn):
    api.add("POST", f"{BASE}/sendMessage", status=400, json={"ok": False, "error_code": 400, "description": "Bad Request"})
    with pytest.raises(Permanent) as info:
        telegram.send_message(conn, "x")
    assert TOKEN not in str(info.value)


def test_post_channel_with_a_photo_sends_it_with_the_text_as_caption(api, conn):
    api.add("POST", f"{BASE}/sendPhoto", json={"ok": True, "result": {}})
    telegram.post_channel(conn, "New release", photo_url="https://site.test/media/projects/mars.png")
    body = body_json(api.requests[0])
    assert (body["chat_id"], body["photo"], body["caption"], body["parse_mode"]) == ("@atlas_news", "https://site.test/media/projects/mars.png", "New release", "HTML")


def test_a_long_caption_is_cut_to_telegrams_limit(api, conn):
    api.add("POST", f"{BASE}/sendPhoto", json={"ok": True, "result": {}})
    telegram.post_channel(conn, "x" * 3000, photo_url="https://site.test/p.png")
    assert len(body_json(api.requests[0])["caption"]) == 1024


def test_a_photo_telegram_cannot_fetch_falls_back_to_text(api, conn):
    api.add("POST", f"{BASE}/sendPhoto", status=400, json={"ok": False, "error_code": 400, "description": "Bad Request: wrong file identifier/HTTP URL specified"})
    api.add("POST", f"{BASE}/sendMessage", json={"ok": True, "result": {}})
    telegram.post_channel(conn, "New release", photo_url="https://site.test/missing.png")
    assert body_json(api.requests[1])["text"] == "New release"
