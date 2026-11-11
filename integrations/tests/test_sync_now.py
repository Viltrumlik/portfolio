from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from integrations.models import Connection, ListeningSnapshot
from jobs.models import Job

pytestmark = pytest.mark.django_db


def test_sync_now_queues_and_runs_the_providers_sync(api, tmp_path):
    Connection.objects.create(provider="lastfm", status="connected", account="alisher", credentials={"api_key": "k"}, config={"username": "alisher"})
    api.add("GET", "https://ws.audioscrobbler.com/2.0/", json={"recenttracks": {"track": [{"name": "Song", "artist": {"#text": "Band"}, "@attr": {"nowplaying": "true"}}]}})
    out = StringIO()
    with override_settings(JOBS_LOCK_FILE=tmp_path / "jobs.lock"):
        call_command("sync_now", "lastfm", stdout=out)
    assert ListeningSnapshot.objects.get().track == "Song"
    assert Job.objects.get(kind="lastfm.poll").status == Job.Status.DONE
    assert "lastfm" in out.getvalue()


def test_sync_now_for_a_disconnected_provider_explains(tmp_path):
    with override_settings(JOBS_LOCK_FILE=tmp_path / "jobs.lock"), pytest.raises(CommandError, match="Connect Last.fm first"):
        call_command("sync_now", "lastfm", stdout=StringIO())


def test_sync_now_rejects_unknown_providers():
    with pytest.raises(CommandError):
        call_command("sync_now", "myspace", stdout=StringIO())
