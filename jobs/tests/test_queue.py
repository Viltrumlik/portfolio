import pytest
from django.utils import timezone

from jobs.models import Job
from jobs.queue import enqueue

pytestmark = pytest.mark.django_db


def test_enqueue_creates_a_queued_job_due_now():
    job = enqueue("github.sync", {"full": True})
    assert job.status == Job.Status.QUEUED
    assert job.payload == {"full": True}
    assert job.run_at <= timezone.now()


def test_enqueue_with_the_same_dedupe_key_returns_the_existing_queued_job():
    first = enqueue("lastfm.poll", dedupe_key="lastfm.poll")
    second = enqueue("lastfm.poll", dedupe_key="lastfm.poll")
    assert first.pk == second.pk
    assert Job.objects.count() == 1
