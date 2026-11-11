import pytest

from automations.events import emit
from automations.models import Event
from jobs.models import Job

pytestmark = pytest.mark.django_db


def test_emit_records_the_event_and_queues_its_dispatch():
    event = emit("contact.submitted", {"name": "Ann"}, source="site")
    assert Event.objects.get(pk=event.pk).payload == {"name": "Ann"}
    job = Job.objects.get(kind="automations.dispatch")
    assert job.payload == {"event_id": event.pk}


def test_emit_with_a_seen_external_id_does_not_duplicate():
    a = emit("github.push", {"repo": "x"}, source="github", external_id="gh-123")
    b = emit("github.push", {"repo": "x"}, source="github", external_id="gh-123")
    assert a.pk == b.pk
    assert Event.objects.count() == 1
    assert Job.objects.filter(kind="automations.dispatch").count() == 1
