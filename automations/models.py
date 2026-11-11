from django.db import models
from django.utils import timezone


class Event(models.Model):
    """Something that happened: github.push, github.release.published, contact.submitted, post.published, sync.failed."""

    type = models.CharField(max_length=80, db_index=True)
    source = models.CharField(max_length=40, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    external_id = models.CharField(max_length=160, null=True, blank=True, unique=True)
    public = models.BooleanField(default=False, help_text="Shown in the public activity feed")
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.type} @ {self.occurred_at:%Y-%m-%d %H:%M}"


class Rule(models.Model):
    class Action(models.TextChoices):
        TELEGRAM_SEND = "telegram.send", "Send me a Telegram message"
        TELEGRAM_POST = "telegram.post_channel", "Post to a Telegram channel"
        WEBHOOK_SEND = "webhook.send", "Send to a webhook"
        RESYNC = "site.resync_projects", "Re-sync projects from GitHub"

    name = models.CharField(max_length=120)
    trigger = models.CharField(max_length=80, help_text="Event type, e.g. github.release.published")
    filters = models.JSONField(default=dict, blank=True, help_text='e.g. {"repo": ["volunteers_bot"], "branch": "main"}')
    action = models.CharField(max_length=40, choices=Action.choices)
    action_config = models.JSONField(default=dict, blank=True, help_text='e.g. {"template": "New release {{repo}}", "hook_id": 1}')
    is_enabled = models.BooleanField(default=False)
    is_builtin = models.BooleanField(default=False)
    run_count = models.PositiveIntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_enabled", "name"]

    def __str__(self):
        return self.name


class RuleRun(models.Model):
    class Status(models.TextChoices):
        OK = "ok", "OK"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="runs")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rule_runs")
    status = models.CharField(max_length=10, choices=Status.choices)
    output = models.TextField(blank=True)
    ran_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ran_at"]
