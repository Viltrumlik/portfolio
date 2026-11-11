"""Queue periodic work, then run due jobs for up to JOBS_RUN_BUDGET_SECONDS. Run it every minute."""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs import registry, runner
from jobs.lock import job_lock

log = logging.getLogger("atlas.jobs")


class Command(BaseCommand):
    help = "Schedule periodic provider work and run due background jobs (one runner at a time)."

    def add_arguments(self, parser):
        parser.add_argument("--budget", type=float, default=None, help="Seconds to spend running jobs.")

    def handle(self, *args, **options):
        budget = options["budget"] if options["budget"] is not None else settings.JOBS_RUN_BUDGET_SECONDS
        with job_lock() as acquired:
            if not acquired:
                self.stdout.write("run_jobs is already running; skipping this run.")
                return
            now = timezone.now()
            for task in registry.periodic_tasks():
                try:
                    task(now)
                except Exception:
                    log.exception("periodic task %s failed", getattr(task, "__name__", task))
            stats = runner.run_due(budget)
            runner.prune()
        self.stdout.write(
            f"done {stats.get('done', 0)} · retry {stats.get('retry', 0)} · failed {stats.get('failed', 0)}"
        )
