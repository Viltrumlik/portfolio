import pytest

from integrations.errors import AuthError, Permanent, RateLimited, Transient
from integrations.models import Connection, ListeningSnapshot
from integrations.providers import lastfm

pytestmark = pytest.mark.django_db

API = "https://ws.audioscrobbler.com/2.0/"


def method_is(name):
    return lambda request: request.url.params.get("method") == name


@pytest.fixture
def conn():
    return Connection.objects.create(provider="lastfm", status="connected", account="alisher", credentials={"api_key": "k123"}, config={"username": "alisher"})


def track(name="Song", artist="Band", *, now_playing=False, uts="1762768800"):
    item = {
        "name": name,
        "artist": {"#text": artist},
        "album": {"#text": "Album"},
        "url": "https://www.last.fm/music/Band/_/Song",
        "image": [{"size": "small", "#text": "https://img/s.png"}, {"size": "extralarge", "#text": "https://img/xl.png"}],
    }
    if now_playing:
        item["@attr"] = {"nowplaying": "true"}
    else:
        item["date"] = {"uts": uts}
    return item


def recent(*tracks):
    return {"recenttracks": {"track": list(tracks), "@attr": {"user": "alisher"}}}


def test_verify_returns_the_user(api):
    api.add("GET", API, json={"user": {"name": "Alisher", "url": "https://www.last.fm/user/Alisher"}}, match=method_is("user.getinfo"))
    assert lastfm.verify("alisher", "k123") == {"name": "Alisher", "url": "https://www.last.fm/user/Alisher"}
    params = api.requests[0].url.params
    assert params["user"] == "alisher" and params["api_key"] == "k123" and params["format"] == "json"


@pytest.mark.parametrize("code", [10, 26])
def test_bad_or_suspended_key_is_an_auth_error(api, code):
    api.add("GET", API, status=403, json={"error": code, "message": "Invalid API key"})
    with pytest.raises(AuthError, match=f"error {code}"):
        lastfm.verify("alisher", "bad")


def test_rate_limit_is_rate_limited_for_a_minute(api):
    api.add("GET", API, status=429, json={"error": 29, "message": "Rate limit exceeded"})
    with pytest.raises(RateLimited) as info:
        lastfm.verify("alisher", "k")
    assert info.value.retry_after_seconds == 60


def test_unknown_user_is_permanent(api):
    api.add("GET", API, status=404, json={"error": 6, "message": "User not found"})
    with pytest.raises(Permanent, match="error 6"):
        lastfm.verify("nobody", "k")


def test_service_trouble_is_transient(api):
    api.add("GET", API, status=503, json={"error": 16, "message": "Temporarily unavailable"})
    with pytest.raises(Transient):
        lastfm.verify("alisher", "k")


def test_poll_records_the_current_track(api, conn):
    api.add("GET", API, json=recent(track(now_playing=True), track("Older")), match=method_is("user.getrecenttracks"))
    snap = lastfm.poll(conn)
    assert (snap.track, snap.artist, snap.album, snap.now_playing) == ("Song", "Band", "Album", True)
    assert snap.image_url == "https://img/xl.png"
    assert api.requests[0].url.params["limit"] == "1"
    conn.refresh_from_db()
    assert conn.last_synced_at is not None


def test_poll_only_records_changes(api, conn):
    api.add("GET", API, json=recent(track(now_playing=True)), times=2)
    api.add("GET", API, json=recent(track()), times=1)
    api.add("GET", API, json=recent(track("Next", now_playing=True)))
    lastfm.poll(conn)
    assert lastfm.poll(conn) is None
    stopped = lastfm.poll(conn)
    assert stopped.now_playing is False and stopped.played_at is not None
    lastfm.poll(conn)
    assert list(ListeningSnapshot.objects.order_by("-id").values_list("track", "now_playing")) == [("Next", True), ("Song", False), ("Song", True)]


def test_poll_keeps_only_the_newest_twenty(api, conn):
    for i in range(25):
        ListeningSnapshot.objects.create(track=f"t{i}")
    api.add("GET", API, json=recent(track("Fresh", now_playing=True)))
    lastfm.poll(conn)
    assert ListeningSnapshot.objects.count() == 20
    assert ListeningSnapshot.objects.filter(track="Fresh").exists()


def test_poll_with_no_history_records_nothing(api, conn):
    api.add("GET", API, json={"recenttracks": {"track": [], "@attr": {}}})
    assert lastfm.poll(conn) is None


def test_poll_accepts_a_single_track_object(api, conn):
    api.add("GET", API, json={"recenttracks": {"track": track(now_playing=True)}})
    assert lastfm.poll(conn).track == "Song"


def test_poll_errors_never_include_the_key(api, conn):
    api.add("GET", API, status=403, json={"error": 10, "message": "Invalid API key"})
    with pytest.raises(AuthError) as info:
        lastfm.poll(conn)
    assert "k123" not in str(info.value)
