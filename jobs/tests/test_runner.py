from datetime import timedelta

import pytest
from django.utils import timezone

from automations.models import Event
from integrations.errors import AuthError, Permanent, RateLimited, Transient
from integrations.models import Connection
from jobs import runner
from jobs.models import Job
from jobs.queue import enqueue

pytestmark = pytest.mark.django_db


def test_registry_returns_the_registered_handler(handlers):
    @handlers.handler("test.echo")
    def echo(payload):
        return payload

    assert handlers.get("test.echo") is echo
    assert handlers.get("test.missing") is None


def test_due_job_runs_and_is_marked_done(handlers):
    seen = []
    handlers.handler("test.ok")(lambda payload: seen.append(payload))
    job = enqueue("test.ok", {"n": 1})

    stats = runner.run_due(10)

    job.refresh_from_db()
    assert seen == [{"n": 1}]
    assert job.status == Job.Status.DONE
    assert job.attempts == 1
    assert job.finished_at is not None
    assert stats["done"] == 1


def test_future_job_is_not_run(handlers):
    seen = []
    handlers.handler("test.ok")(lambda payload: seen.append(payload))
    enqueue("test.ok", run_at=timezone.now() + timedelta(minutes=5))
    runner.run_due(10)
    assert seen == []


def test_claim_is_atomic(handlers):
    job = enqueue("test.ok")
    assert runner.claim(job, timezone.now()) is True
    assert runner.claim(job, timezone.now()) is False


def test_zero_budget_runs_nothing(handlers):
    seen = []
    handlers.handler("test.ok")(lambda payload: seen.append(payload))
    enqueue("test.ok")
    runner.run_due(0)
    assert seen == []


@pytest.mark.parametrize("exc", [AuthError("GitHub rejected the token."), Permanent("Bad request.")])
def test_auth_and_permanent_errors_fail_immediately(handlers, exc):
    def boom(payload):
        raise exc

    handlers.handler("test.boom")(boom)
    job = enqueue("test.boom")
    runner.run_due(10)
    job.refresh_from_db()
    assert job.status == Job.Status.FAILED
    assert job.last_error == str(exc)


def test_rate_limited_requeues_after_retry_after_without_using_an_attempt(handlers):
    def slow(payload):
        raise RateLimited(120)

    handlers.handler("test.slow")(slow)
    now = timezone.now()
    job = enqueue("test.slow", run_at=now)
    runner.run_due(10, now=now)
    job.refresh_from_db()
    assert job.status == Job.Status.QUEUED
    assert job.run_at == now + timedelta(seconds=120)
    assert job.attempts == 0


@pytest.mark.parametrize("exc", [Transient("GitHub did not answer in time."), ValueError("bug")])
def test_transient_and_unexpected_errors_retry_with_backoff(handlers, exc):
    def flaky(payload):
        raise exc

    handlers.handler("test.flaky")(flaky)
    now = timezone.now()
    job = enqueue("test.flaky", run_at=now)

    runner.run_due(10, now=now)
    job.refresh_from_db()
    assert job.status == Job.Status.QUEUED
    assert job.run_at == now + timedelta(seconds=60)
    assert str(exc) in job.last_error

    later = job.run_at
    runner.run_due(10, now=later)
    job.refresh_from_db()
    assert job.run_at == later + timedelta(seconds=300)
    assert job.attempts == 2


def test_job_fails_after_max_attempts(handlers):
    def flaky(payload):
        raise Transient("down")

    handlers.handler("test.flaky")(flaky)
    now = timezone.now()
    job = enqueue("test.flaky", run_at=now, max_attempts=2)
    runner.run_due(10, now=now)
    job.refresh_from_db()
    runner.run_due(10, now=job.run_at)
    job.refresh_from_db()
    assert job.status == Job.Status.FAILED
    assert job.attempts == 2


def test_unknown_kind_fails(handlers):
    job = enqueue("test.nobody-home")
    runner.run_due(10)
    job.refresh_from_db()
    assert job.status == Job.Status.FAILED
    assert "test.nobody-home" in job.last_error


def test_jobs_queued_by_a_handler_run_in_the_same_pass(handlers):
    seen = []
    handlers.handler("test.first")(lambda payload: enqueue("test.second"))
    handlers.handler("test.second")(lambda payload: seen.append("second"))
    enqueue("test.first")
    runner.run_due(10)
    assert seen == ["second"]


def test_stale_running_jobs_are_requeued(handlers):
    seen = []
    handlers.handler("test.ok")(lambda payload: seen.append(1))
    now = timezone.now()
    job = enqueue("test.ok", run_at=now - timedelta(hours=1))
    Job.objects.filter(pk=job.pk).update(status=Job.Status.RUNNING, locked_at=now - timedelta(hours=1))
    runner.run_due(10, now=now)
    job.refresh_from_db()
    assert seen == [1]
    assert job.status == Job.Status.DONE


def test_failed_provider_job_flags_the_connection_and_emits_sync_failed(handlers):
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})

    def boom(payload):
        raise AuthError("GitHub rejected the token.", code="401")

    handlers.handler("github.sync")(boom)
    enqueue("github.sync")
    runner.run_due(10)

    conn = Connection.objects.get(provider="github")
    assert conn.status == Connection.Status.ERROR
    assert conn.last_error == "GitHub rejected the token."
    assert conn.error_code == "401"
    event = Event.objects.get(type="sync.failed")
    assert event.payload == {"provider": "github", "error": "GitHub rejected the token."}
    assert event.source == "site"


def test_failed_webhook_job_emits_sync_failed_without_a_connection(handlers):
    def boom(payload):
        raise Permanent("Webhook n8n answered 404.")

    handlers.handler("webhook.deliver")(boom)
    source = Event.objects.create(type="contact.submitted")
    enqueue("webhook.deliver", {"hook_id": 1, "event_id": source.pk})
    runner.run_due(10)
    assert Event.objects.get(type="sync.failed").payload["provider"] == "webhook"


def test_jobs_handling_a_sync_failed_event_never_emit_another(handlers):
    def boom(payload):
        raise Permanent("Webhook n8n answered 404.")

    handlers.handler("webhook.deliver")(boom)
    handlers.handler("automations.dispatch")(lambda payload: None)
    original = Event.objects.create(type="sync.failed", payload={"provider": "github", "error": "x"})
    enqueue("webhook.deliver", {"hook_id": 1, "event_id": original.pk})
    runner.run_due(10)
    assert Event.objects.filter(type="sync.failed").count() == 1


def test_jobs_triggered_by_sync_failed_never_emit_another(handlers):
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})

    def boom(payload):
        raise AuthError("GitHub rejected the token.")

    handlers.handler("github.sync")(boom)
    enqueue("github.sync", {"trigger": "sync.failed"})
    runner.run_due(10)
    assert not Event.objects.filter(type="sync.failed").exists()
    assert Connection.objects.get(provider="github").status == Connection.Status.ERROR


def test_retrying_provider_job_does_not_flag_the_connection(handlers):
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})

    def flaky(payload):
        raise Transient("Last.fm did not answer in time.")

    handlers.handler("lastfm.poll")(flaky)
    enqueue("lastfm.poll")
    runner.run_due(10)
    assert Connection.objects.get(provider="lastfm").status == Connection.Status.CONNECTED
    assert not Event.objects.filter(type="sync.failed").exists()


def test_prune_removes_old_finished_jobs():
    now = timezone.now()
    old = enqueue("test.old")
    Job.objects.filter(pk=old.pk).update(status=Job.Status.DONE, finished_at=now - timedelta(days=8))
    fresh = enqueue("test.fresh")
    Job.objects.filter(pk=fresh.pk).update(status=Job.Status.DONE, finished_at=now - timedelta(hours=1))
    queued = enqueue("test.queued")
    runner.prune(now=now)
    assert set(Job.objects.values_list("pk", flat=True)) == {fresh.pk, queued.pk}
