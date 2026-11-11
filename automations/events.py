"""Record that something happened. Rules react to events via the `automations.dispatch` job."""
from django.db import IntegrityError, transaction

from jobs.queue import enqueue

from .models import Event


def emit(type, payload=None, *, source="site", external_id=None, public=False, occurred_at=None):
    """Store an event (once per external_id) and queue its dispatch to matching rules."""
    if external_id:
        existing = Event.objects.filter(external_id=external_id).first()
        if existing:
            return existing
    fields = {"type": type, "payload": payload or {}, "source": source, "external_id": external_id, "public": public}
    if occurred_at:
        fields["occurred_at"] = occurred_at
    try:
        with transaction.atomic():
            event = Event.objects.create(**fields)
            enqueue("automations.dispatch", {"event_id": event.pk})
    except IntegrityError:  # a concurrent writer stored the same external_id first
        return Event.objects.get(external_id=external_id)
    return event
