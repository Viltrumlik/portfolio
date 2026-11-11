"""Queue a provider's sync and run it now: `manage.py sync_now github`."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from integrations import actions
from integrations.errors import IntegrationError
from integrations.models import Connection
from jobs import runner
from jobs.lock import job_lock


class Command(BaseCommand):
    help = "Queue a sync for a connected provider and run due jobs now."

    def add_arguments(self, parser):
        parser.add_argument("provider", choices=[p for p, _ in Connection.Provider.choices])

    def handle(self, *args, provider, **options):
        try:
            job = actions.request_sync(provider)
        except IntegrationError as exc:
            raise CommandError(str(exc)) from exc
        with job_lock() as acquired:
            if not acquired:
                self.stdout.write(f"Queued {job.kind} for {provider}; the running job worker will pick it up.")
                return
            runner.run_due(settings.JOBS_RUN_BUDGET_SECONDS)
        job.refresh_from_db()
        conn = Connection.objects.get(provider=provider)
        line = f"{provider}: {job.kind} {job.status}"
        if job.last_error:
            line += f" ({job.last_error})"
        self.stdout.write(f"{line}; connection {conn.status}.")
