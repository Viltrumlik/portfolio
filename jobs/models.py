from django.db import models
from django.utils import timezone


class Job(models.Model):
    """A unit of background work, run by `manage.py run_jobs`."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    kind = models.CharField(max_length=80, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    run_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    last_error = models.TextField(blank=True)
    dedupe_key = models.CharField(max_length=200, null=True, blank=True, unique=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["run_at", "id"]
        indexes = [models.Index(fields=["status", "run_at"])]

    def __str__(self):
        return f"{self.kind} #{self.pk} ({self.status})"
