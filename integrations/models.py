from django.db import models

from .fields import EncryptedJSONField


class Connection(models.Model):
    """One connected service. Secrets live in `credentials` (encrypted)."""

    class Provider(models.TextChoices):
        GITHUB = "github", "GitHub"
        TELEGRAM = "telegram", "Telegram"
        LASTFM = "lastfm", "Last.fm"

    class Status(models.TextChoices):
        OFF = "off", "Not connected"
        SYNCING = "syncing", "Syncing"
        CONNECTED = "connected", "Connected"
        ERROR = "error", "Needs attention"

    provider = models.CharField(max_length=20, choices=Provider.choices, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OFF)
    account = models.CharField(max_length=200, blank=True)
    credentials = EncryptedJSONField(default=dict, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    config = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    error_code = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_provider_display()} ({self.status})"


class Repo(models.Model):
    github_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=300, unique=True)
    description = models.TextField(blank=True)
    url = models.URLField()
    homepage = models.URLField(blank=True)
    language = models.CharField(max_length=60, blank=True)
    languages = models.JSONField(default=dict, blank=True)
    stars = models.PositiveIntegerField(default=0)
    forks = models.PositiveIntegerField(default=0)
    topics = models.JSONField(default=list, blank=True)
    is_fork = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    pushed_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pinned", "-pushed_at"]

    def __str__(self):
        return self.full_name


class ContributionDay(models.Model):
    date = models.DateField(unique=True)
    count = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["date"]


class ListeningSnapshot(models.Model):
    track = models.CharField(max_length=300)
    artist = models.CharField(max_length=300, blank=True)
    album = models.CharField(max_length=300, blank=True)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    now_playing = models.BooleanField(default=False)
    played_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fetched_at"]


class SyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        OK = "ok", "OK"
        FAILED = "failed", "Failed"

    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name="runs")
    kind = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    items_changed = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]


class InboundDelivery(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSED = "processed", "Processed"
        IGNORED = "ignored", "Ignored"
        FAILED = "failed", "Failed"

    provider = models.CharField(max_length=20)
    delivery_id = models.CharField(max_length=120, unique=True)
    event = models.CharField(max_length=60)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]


class OutboundHook(models.Model):
    """An outgoing webhook (n8n, Make, Zapier). Payloads are HMAC-signed with `secret`."""

    name = models.CharField(max_length=120)
    url = models.URLField()
    secret = EncryptedJSONField(default=dict, blank=True)
    events = models.JSONField(default=list, blank=True, help_text="Event types to send, e.g. ['contact.submitted']")
    is_active = models.BooleanField(default=True)
    last_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
