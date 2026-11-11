"""Connection health: mark a provider as working or as needing attention."""
from django.utils import timezone

from automations.events import emit

from .models import Connection

PROVIDERS = ("github", "lastfm", "telegram", "webhook")


def record_failure(provider, exc, *, notify=True):
    """Flag the provider's connection as `error` and (unless `notify` is False) emit sync.failed."""
    message = str(exc) or exc.__class__.__name__
    code = getattr(exc, "code", "")
    Connection.objects.filter(provider=provider).exclude(status=Connection.Status.OFF).update(
        status=Connection.Status.ERROR, last_error=message, error_code=code[:60], updated_at=timezone.now()
    )
    if notify:
        emit("sync.failed", {"provider": provider, "error": message}, source="site")


def record_success(connection, *, synced=True):
    """Mark the connection as connected and clear any error."""
    fields = {"status": Connection.Status.CONNECTED, "last_error": "", "error_code": "", "updated_at": timezone.now()}
    if synced:
        fields["last_synced_at"] = timezone.now()
    Connection.objects.filter(pk=connection.pk).update(**fields)
    for name, value in fields.items():
        setattr(connection, name, value)
