from datetime import timedelta

import pytest
from django.utils import timezone

from integrations.models import Connection
from integrations.schedule import schedule_periodic
from jobs.models import Job

pytestmark = pytest.mark.django_db


def kinds():
    return sorted(Job.objects.values_list("kind", flat=True))


def test_nothing_is_scheduled_without_connections():
    schedule_periodic(timezone.now())
    assert kinds() == []


def test_connected_github_gets_a_full_sync_and_an_events_poll():
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    schedule_periodic(timezone.now())
    assert kinds() == ["github.events", "github.sync"]


def test_full_sync_waits_for_next_sync_at():
    now = timezone.now()
    Connection.objects.create(
        provider="github", status="connected", credentials={"token": "t"}, next_sync_at=now + timedelta(minutes=30)
    )
    schedule_periodic(now)
    assert kinds() == ["github.events"]


def test_disconnected_or_failing_providers_are_not_polled():
    Connection.objects.create(provider="github", status="error", credentials={"token": "t"})
    Connection.objects.create(provider="lastfm", status="off", credentials={})
    schedule_periodic(timezone.now())
    assert kinds() == []


def test_scheduling_twice_does_not_duplicate():
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})
    now = timezone.now()
    schedule_periodic(now)
    schedule_periodic(now + timedelta(seconds=5))
    assert kinds() == ["lastfm.poll"]


def test_lastfm_is_polled_every_minute():
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})
    now = timezone.now()
    schedule_periodic(now)
    Job.objects.update(status=Job.Status.DONE, finished_at=now)
    schedule_periodic(now + timedelta(seconds=30))
    assert Job.objects.count() == 1
    schedule_periodic(now + timedelta(seconds=60))
    assert Job.objects.filter(status=Job.Status.QUEUED, kind="lastfm.poll").count() == 1
    assert Job.objects.count() == 2


def test_github_events_are_polled_every_five_minutes():
    now = timezone.now()
    Connection.objects.create(
        provider="github", status="connected", credentials={"token": "t"}, next_sync_at=now + timedelta(hours=1)
    )
    schedule_periodic(now)
    Job.objects.update(status=Job.Status.DONE, finished_at=now)
    schedule_periodic(now + timedelta(minutes=2))
    assert Job.objects.count() == 1
    schedule_periodic(now + timedelta(minutes=5))
    assert Job.objects.count() == 2
