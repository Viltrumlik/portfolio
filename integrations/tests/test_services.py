from datetime import date, timedelta

import pytest
from django.utils import timezone

from automations.models import Event
from integrations import services
from integrations.models import Connection, ContributionDay, ListeningSnapshot, Repo

pytestmark = pytest.mark.django_db


@pytest.fixture
def github_on():
    return Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "ghp_abcdef1234", "webhook_secret": "whsec_zz"}, scopes=["public_repo"])


@pytest.fixture
def lastfm_on():
    return Connection.objects.create(provider="lastfm", status="connected", account="alisher", credentials={"api_key": "0123456789ab91ab"}, last_synced_at=timezone.now())


def make_repo(github_id, name, *, pinned=False, fork=False, archived=False, days_ago=1):
    return Repo.objects.create(
        github_id=github_id, name=name, full_name=f"A1isherDev/{name}", url=f"https://github.com/A1isherDev/{name}",
        pinned=pinned, is_fork=fork, is_archived=archived, pushed_at=timezone.now() - timedelta(days=days_ago),
    )


# --- contributions --------------------------------------------------------------------


def test_contribution_days_cover_whole_weeks_ending_today(github_on):
    today = date(2026, 11, 11)  # a Wednesday
    for offset in range(400):
        ContributionDay.objects.create(date=today - timedelta(days=offset), count=offset % 5, level=offset % 5)
    days = services.contribution_days(weeks=2, today=today)
    assert days[0]["date"] == date(2026, 11, 1)  # the Sunday that starts the first week
    assert days[-1]["date"] == today
    assert len(days) == 11
    assert set(days[0]) == {"date", "count", "level"}


def test_contribution_total_sums_the_last_year(github_on):
    today = date(2026, 11, 11)
    ContributionDay.objects.create(date=today, count=3)
    ContributionDay.objects.create(date=today - timedelta(days=364), count=4)
    ContributionDay.objects.create(date=today - timedelta(days=365), count=100)
    assert services.contribution_total(days=365, today=today) == 7


def test_github_helpers_are_empty_when_github_is_disconnected():
    ContributionDay.objects.create(date=date.today(), count=3)
    make_repo(1, "atlas", pinned=True)
    assert services.contribution_days() == []
    assert services.contribution_total() is None
    assert services.pinned_repos() == []


# --- repos ----------------------------------------------------------------------------


def test_pinned_repos_come_first_then_recent_own_repos(github_on):
    make_repo(1, "recent", days_ago=1)
    make_repo(2, "pinned-old", pinned=True, days_ago=100)
    make_repo(3, "fork", fork=True, days_ago=0)
    make_repo(4, "archived", archived=True, days_ago=0)
    make_repo(5, "older", days_ago=10)
    assert [r.name for r in services.pinned_repos(limit=3)] == ["pinned-old", "recent", "older"]


# --- listening ------------------------------------------------------------------------


def test_now_listening_returns_the_playing_track(lastfm_on):
    ListeningSnapshot.objects.create(track="Song", artist="Band", album="LP", now_playing=True)
    now = services.now_listening()
    assert now["track"] == "Song" and now["artist"] == "Band" and now["now_playing"] is True


def test_now_listening_returns_a_recent_track_that_stopped(lastfm_on):
    ListeningSnapshot.objects.create(track="Song", now_playing=False, played_at=timezone.now() - timedelta(minutes=20))
    assert services.now_listening(max_age_minutes=60)["now_playing"] is False


def test_now_listening_is_none_when_stale_or_disconnected(lastfm_on):
    ListeningSnapshot.objects.create(track="Old", now_playing=False, played_at=timezone.now() - timedelta(hours=3))
    assert services.now_listening(max_age_minutes=60) is None
    ListeningSnapshot.objects.create(track="Playing", now_playing=True)
    Connection.objects.filter(pk=lastfm_on.pk).update(last_synced_at=timezone.now() - timedelta(hours=2))
    assert services.now_listening(max_age_minutes=60) is None
    Connection.objects.filter(pk=lastfm_on.pk).update(status="off", last_synced_at=timezone.now())
    assert services.now_listening() is None


def test_now_listening_with_no_snapshots_is_none(lastfm_on):
    assert services.now_listening() is None


# --- public events --------------------------------------------------------------------


def test_recent_public_events_are_newest_first_and_public_only():
    now = timezone.now()
    Event.objects.create(type="github.push", source="github", public=True, occurred_at=now - timedelta(hours=2), payload={"repo": "A1isherDev/atlas", "branch": "main", "commits": 3, "url": "https://github.com/x"})
    Event.objects.create(type="github.release.published", source="github", public=True, occurred_at=now - timedelta(hours=1), payload={"repo": "A1isherDev/atlas", "tag": "v1.0", "url": "https://github.com/r"})
    Event.objects.create(type="contact.submitted", source="site", public=False, occurred_at=now, payload={"email": "secret@example.com"})
    events = services.recent_public_events(limit=10)
    assert [e["type"] for e in events] == ["github.release.published", "github.push"]
    assert events[0]["code"] == "GH"
    assert events[0]["text"] == "Released v1.0 of A1isherDev/atlas"
    assert events[1]["text"] == "Pushed 3 commits to A1isherDev/atlas (main)"
    assert events[1]["url"] == "https://github.com/x"


def test_push_without_a_count_reads_naturally():
    Event.objects.create(type="github.push", source="github", public=True, payload={"repo": "A1isherDev/atlas", "branch": "dev", "commits": None})
    assert services.recent_public_events()[0]["text"] == "Pushed to A1isherDev/atlas (dev)"


# --- studio summary -------------------------------------------------------------------


def test_connection_summary_lists_every_provider_with_masked_secrets(github_on, lastfm_on):
    Connection.objects.filter(pk=github_on.pk).update(status="error", last_error="GitHub rejected the token.", error_code="401")
    summary = services.connection_summary()
    assert set(summary) == {"github", "telegram", "lastfm"}
    gh = summary["github"]
    assert gh["status"] == "error"
    assert gh["status_label"] == "Needs attention"
    assert gh["account"] == "A1isherDev"
    assert gh["last_error"] == "GitHub rejected the token."
    assert gh["error_code"] == "401"
    assert gh["secret"] == "•••• 1234"
    assert gh["scopes"] == ["public_repo"]
    assert gh["webhook_secret_set"] is True
    assert summary["lastfm"]["secret"] == "•••• 91ab"
    assert summary["telegram"]["status"] == "off"
    flat = repr(summary)
    assert "ghp_abcdef1234" not in flat and "whsec_zz" not in flat and "0123456789ab91ab" not in flat
