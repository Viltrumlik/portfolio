"""Last.fm: verify a user + API key and record what is playing now."""
from datetime import datetime, timezone as dt_timezone

from .. import http
from ..errors import AuthError, Permanent, RateLimited, Transient
from ..health import record_success
from ..models import ListeningSnapshot

API = "https://ws.audioscrobbler.com/2.0/"
SERVICE = "Last.fm"
KEEP = 20

AUTH_ERRORS = {10, 26}  # invalid key, suspended key
TRANSIENT_ERRORS = {8, 11, 16}  # operation failed, service offline, temporarily unavailable


def _call(method, api_key, **params):
    response = http.request(
        "GET", API, service=SERVICE, params={"method": method, "api_key": api_key, "format": "json", **params}
    )
    try:
        body = response.json()
    except ValueError:
        body = {}
    code = body.get("error") if isinstance(body, dict) else None
    if code is None and response.status_code == 200:
        return body
    message = str(body.get("message") or f"HTTP {response.status_code}").replace(api_key, "•••") if isinstance(body, dict) else ""
    if code in AUTH_ERRORS:
        raise AuthError(f"Last.fm rejected the API key (error {code}). Paste a new key to resume syncing.", code=f"lastfm-{code}")
    if code == 29:
        raise RateLimited(60, "Last.fm's rate limit was hit (error 29). It will retry in a minute.", code="lastfm-29")
    if code in TRANSIENT_ERRORS or response.status_code >= 500:
        raise Transient(f"Last.fm is having trouble (error {code or response.status_code}). It will retry.", code=f"lastfm-{code or response.status_code}")
    if code == 6:
        raise Permanent(f"Last.fm has no user named {params.get('user', '')} (error 6). Check the username.", code="lastfm-6")
    raise Permanent(f"Last.fm refused the request (error {code or response.status_code}): {message}", code=f"lastfm-{code or response.status_code}")


def verify(username, api_key):
    """user.getInfo -> {"name", "url"}."""
    user = _call("user.getinfo", api_key, user=username)["user"]
    return {"name": user.get("name", username), "url": user.get("url", "")}


def _image(item):
    images = {i.get("size"): i.get("#text", "") for i in item.get("image") or []}
    return images.get("extralarge") or images.get("large") or next((v for v in reversed(list(images.values())) if v), "")


def poll(connection):
    """Record the latest track when the track or the now-playing flag changed. Returns the new snapshot or None."""
    username = (connection.config or {}).get("username") or connection.account
    body = _call("user.getrecenttracks", connection.credentials["api_key"], user=username, limit=1)
    tracks = (body.get("recenttracks") or {}).get("track") or []
    if isinstance(tracks, dict):
        tracks = [tracks]
    record_success(connection)
    if not tracks:
        return None
    item = tracks[0]
    now_playing = (item.get("@attr") or {}).get("nowplaying") == "true"
    name, artist = item.get("name", ""), (item.get("artist") or {}).get("#text", "")
    latest = ListeningSnapshot.objects.order_by("-fetched_at", "-id").first()
    if latest and (latest.track, latest.artist, latest.now_playing) == (name, artist, now_playing):
        return None
    uts = (item.get("date") or {}).get("uts")
    snapshot = ListeningSnapshot.objects.create(
        track=name[:300],
        artist=artist[:300],
        album=(item.get("album") or {}).get("#text", "")[:300],
        url=item.get("url", ""),
        image_url=_image(item),
        now_playing=now_playing,
        played_at=datetime.fromtimestamp(int(uts), tz=dt_timezone.utc) if uts else None,
    )
    stale = list(ListeningSnapshot.objects.order_by("-fetched_at", "-id").values_list("pk", flat=True)[KEEP:])
    ListeningSnapshot.objects.filter(pk__in=stale).delete()
    return snapshot
