"""Queue background work. Handlers register with jobs.registry and run via `manage.py run_jobs`."""
from django.db import transaction
from django.utils import timezone

from .models import Job


def enqueue(kind, payload=None, *, run_at=None, dedupe_key=None, max_attempts=5):
    """Queue a job. With `dedupe_key`, an already-queued job with that key is returned instead."""
    with transaction.atomic():
        if dedupe_key:
            existing = Job.objects.filter(dedupe_key=dedupe_key).first()
            if existing and existing.status == Job.Status.QUEUED:
                return existing
            if existing:  # finished or running: free the key for the next run
                Job.objects.filter(pk=existing.pk).update(dedupe_key=None)
        return Job.objects.create(
            kind=kind,
            payload=payload or {},
            run_at=run_at or timezone.now(),
            dedupe_key=dedupe_key,
            max_attempts=max_attempts,
        )
