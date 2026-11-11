import fcntl
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from jobs.models import Job
from jobs.queue import enqueue

pytestmark = pytest.mark.django_db


def test_run_jobs_schedules_periodic_work_then_runs_due_jobs(handlers, tmp_path):
    order = []
    handlers.periodic(lambda now: order.append("schedule"))
    handlers.handler("test.ok")(lambda payload: order.append("run"))
    enqueue("test.ok")
    try:
        with override_settings(JOBS_LOCK_FILE=tmp_path / "jobs.lock"):
            call_command("run_jobs", stdout=StringIO())
    finally:
        handlers._periodic.pop()
    assert order == ["schedule", "run"]
    assert Job.objects.get().status == Job.Status.DONE


def test_run_jobs_exits_quietly_when_another_run_holds_the_lock(handlers, tmp_path):
    seen = []
    handlers.handler("test.ok")(lambda payload: seen.append(1))
    enqueue("test.ok")
    lock_path = tmp_path / "jobs.lock"
    with open(lock_path, "a") as held:
        fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        out = StringIO()
        with override_settings(JOBS_LOCK_FILE=lock_path):
            call_command("run_jobs", stdout=out)
    assert seen == []
    assert "already running" in out.getvalue()


def test_a_failing_scheduler_does_not_stop_the_run(handlers, tmp_path):
    seen = []

    def broken(now):
        raise RuntimeError("bad scheduler")

    handlers.periodic(broken)
    handlers.handler("test.ok")(lambda payload: seen.append(1))
    enqueue("test.ok")
    try:
        with override_settings(JOBS_LOCK_FILE=tmp_path / "jobs.lock"):
            call_command("run_jobs", stdout=StringIO())
    finally:
        handlers._periodic.remove(broken)
    assert seen == [1]
