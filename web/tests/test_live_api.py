import datetime as dt

import pytest
from django.utils import timezone

from automations.models import Event
from content.models import Profile
from integrations.models import ListeningSnapshot

from . import factories as f

pytestmark = pytest.mark.django_db


def test_now_json_without_listening(client):
    f.profile()
    r = client.get("/api/live/now.json")
    assert r.status_code == 200 and r["Content-Type"] == "application/json"
    assert r.json() == {"listening": None, "availability": {"status": "available", "label": "Available for work"}}


def test_now_json_with_fresh_snapshot_and_note(client):
    f.profile(availability=Profile.Availability.BUSY, availability_note="Booked until December")
    played = timezone.now() - dt.timedelta(minutes=4)
    ListeningSnapshot.objects.create(track="Teardrop", artist="Massive Attack", played_at=played)
    data = client.get("/api/live/now.json").json()
    assert data["availability"] == {"status": "busy", "label": "Booked until December"}
    assert data["listening"]["track"] == "Teardrop"
    assert data["listening"]["artist"] == "Massive Attack"
    assert data["listening"]["played"] == "4 min ago"
    assert data["listening"]["now_playing"] is False


def test_now_json_drops_old_tracks(client):
    f.profile()
    ListeningSnapshot.objects.create(track="Yesterday", played_at=timezone.now() - dt.timedelta(hours=3))
    assert client.get("/api/live/now.json").json()["listening"] is None


def test_activity_json_lists_latest_ten_public_events(client):
    f.profile()
    now = timezone.now()
    for i in range(12):
        Event.objects.create(type="github.push", source="github", public=True,
                             payload={"repo": f"a1/r{i}", "commits": 1}, occurred_at=now - dt.timedelta(minutes=i))
    Event.objects.create(type="contact.submitted", source="site", public=False, payload={"name": "Private"})
    data = client.get("/api/live/activity.json").json()
    assert len(data["items"]) == 10
    assert data["items"][0]["text"] == "Pushed 1 commit to a1/r0"
    assert data["items"][0]["code"] == "GH"
    assert all("Private" not in item["text"] for item in data["items"])
    assert set(data["items"][0]) >= {"time", "datetime", "code", "source", "text", "meta", "tone"}
