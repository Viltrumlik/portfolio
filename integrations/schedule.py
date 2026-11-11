"""Periodic work for connected providers, queued by `manage.py run_jobs` each minute."""
from datetime import timedelta

from django.utils import timezone

from jobs.models import Job
from jobs.queue import enqueue
from jobs.registry import periodic

from .models import Connection

ACTIVE = (Connection.Status.CONNECTED, Connection.Status.SYNCING)
GITHUB_EVENTS_EVERY = 300
LASTFM_EVERY = 60


@periodic
def schedule_periodic(now=None):
    """GitHub full sync when next_sync_at is due, GitHub events every 5 min, Last.fm every minute."""
    now = now or timezone.now()
    active = {c.provider: c for c in Connection.objects.filter(status__in=ACTIVE)}
    github = active.get("github")
    if github and github.credentials.get("token"):
        if github.next_sync_at is None or github.next_sync_at <= now:
            _once("github.sync", now)
        _every("github.events", GITHUB_EVENTS_EVERY, now)
    lastfm = active.get("lastfm")
    if lastfm and lastfm.credentials.get("api_key"):
        _every("lastfm.poll", LASTFM_EVERY, now)


def _pending(kind):
    return Job.objects.filter(kind=kind, status__in=[Job.Status.QUEUED, Job.Status.RUNNING]).exists()


def _once(kind, now):
    if not _pending(kind):
        enqueue(kind, run_at=now, dedupe_key=kind)


def _every(kind, seconds, now):
    if _pending(kind):
        return
    # 10% slack so a timer that fires a little early does not skip a whole period.
    if Job.objects.filter(kind=kind, run_at__gt=now - timedelta(seconds=seconds * 0.9)).exists():
        return
    enqueue(kind, run_at=now, dedupe_key=kind)
