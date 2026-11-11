"""Run due jobs. Called by `manage.py run_jobs` (one process at a time, under a file lock)."""
import logging
import time
from collections import Counter
from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from integrations.errors import AuthError, IntegrationError, Permanent, RateLimited

from . import registry
from .models import Job

log = logging.getLogger("atlas.jobs")

BACKOFF_SECONDS = [60, 300, 1800, 7200, 21600]
STALE_AFTER = timedelta(minutes=10)
PROVIDER_PREFIXES = ("github", "lastfm", "telegram", "webhook")
KEEP_DONE = timedelta(days=7)
KEEP_FAILED = timedelta(days=30)


def claim(job, now):
    """Atomically move a queued job to running. False if another worker got it first."""
    return bool(
        Job.objects.filter(pk=job.pk, status=Job.Status.QUEUED).update(
            status=Job.Status.RUNNING, locked_at=now, attempts=F("attempts") + 1
        )
    )


def run_due(budget_seconds, now=None):
    """Run queued jobs whose run_at has passed until none are left or the budget is spent."""
    started = time.monotonic()
    stats = Counter()
    _requeue_stale(now or timezone.now())
    tried = set()
    while time.monotonic() - started < budget_seconds:
        current = now or timezone.now()
        job = (
            Job.objects.filter(status=Job.Status.QUEUED, run_at__lte=current)
            .exclude(pk__in=tried)
            .order_by("run_at", "id")
            .first()
        )
        if job is None:
            break
        tried.add(job.pk)
        if not claim(job, current):
            continue
        job.refresh_from_db()
        stats[run_job(job, current)] += 1
    return stats


def run_job(job, now):
    """Run one claimed job and record the outcome. Returns 'done', 'retry' or 'failed'."""
    fn = registry.get(job.kind)
    if fn is None:
        _fail(job, f"No handler is registered for {job.kind}.", None, now)
        return "failed"
    try:
        fn(job.payload)
    except (AuthError, Permanent) as exc:
        _fail(job, str(exc), exc, now)
        return "failed"
    except RateLimited as exc:
        _requeue(job, now + timedelta(seconds=exc.retry_after_seconds), str(exc), refund_attempt=True)
        return "retry"
    except Exception as exc:  # Transient, and anything unexpected: retry with backoff
        message = str(exc) if isinstance(exc, IntegrationError) else f"{exc.__class__.__name__}: {exc}"
        if not isinstance(exc, IntegrationError):
            log.exception("job %s #%s raised", job.kind, job.pk)
        if job.attempts >= job.max_attempts:
            _fail(job, message, exc, now)
            return "failed"
        delay = BACKOFF_SECONDS[min(job.attempts, len(BACKOFF_SECONDS)) - 1]
        _requeue(job, now + timedelta(seconds=delay), message)
        return "retry"
    Job.objects.filter(pk=job.pk).update(status=Job.Status.DONE, finished_at=now, locked_at=None, last_error="")
    return "done"


def prune(now=None):
    """Delete finished jobs older than a week (failed ones after a month)."""
    now = now or timezone.now()
    Job.objects.filter(status=Job.Status.DONE, finished_at__lt=now - KEEP_DONE).delete()
    Job.objects.filter(status=Job.Status.FAILED, finished_at__lt=now - KEEP_FAILED).delete()


def _requeue(job, run_at, message, refund_attempt=False):
    fields = {"status": Job.Status.QUEUED, "run_at": run_at, "locked_at": None, "last_error": message}
    if refund_attempt:
        fields["attempts"] = F("attempts") - 1
    Job.objects.filter(pk=job.pk).update(**fields)


def _fail(job, message, exc, now):
    Job.objects.filter(pk=job.pk).update(status=Job.Status.FAILED, finished_at=now, locked_at=None, last_error=message)
    log.warning("job %s #%s failed: %s", job.kind, job.pk, message)
    provider = job.kind.split(".", 1)[0]
    if provider in PROVIDER_PREFIXES and exc is not None:
        from integrations.health import record_failure

        record_failure(provider, exc, notify=not _handles_sync_failed(job))


def _handles_sync_failed(job):
    """True when the job was itself acting on a sync.failed event (so it must not emit another)."""
    payload = job.payload or {}
    if payload.get("trigger") == "sync.failed":
        return True
    event_id = payload.get("event_id")
    if event_id:
        from automations.models import Event

        return Event.objects.filter(pk=event_id, type="sync.failed").exists()
    return False


def _requeue_stale(now):
    """A job left `running` past STALE_AFTER belongs to a worker that died; put it back in the queue."""
    Job.objects.filter(status=Job.Status.RUNNING, locked_at__lt=now - STALE_AFTER).update(
        status=Job.Status.QUEUED, locked_at=None, run_at=now
    )
