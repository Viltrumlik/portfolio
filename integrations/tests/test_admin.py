import pytest
from django.contrib import admin

from automations.models import Event, Rule, RuleRun
from integrations.models import Connection, ContributionDay, InboundDelivery, ListeningSnapshot, OutboundHook, Repo, SyncRun
from jobs.models import Job

pytestmark = pytest.mark.django_db

MODELS = [Job, Connection, Repo, ContributionDay, ListeningSnapshot, SyncRun, InboundDelivery, OutboundHook, Event, Rule, RuleRun]


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
def test_models_are_registered_and_listable(admin_client, model):
    assert admin.site.is_registered(model)
    url = f"/admin/{model._meta.app_label}/{model._meta.model_name}/"
    assert admin_client.get(url).status_code == 200


def test_connection_admin_never_shows_credentials(admin_client):
    conn = Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "ghp_supersecret9999"})
    page = admin_client.get(f"/admin/integrations/connection/{conn.pk}/change/")
    assert page.status_code == 200
    assert b"ghp_supersecret9999" not in page.content
    assert b"A1isherDev" in page.content


def test_outbound_hook_admin_never_shows_the_secret(admin_client):
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/h", secret={"secret": "hook-secret-777"})
    page = admin_client.get(f"/admin/integrations/outboundhook/{hook.pk}/change/")
    assert page.status_code == 200
    assert b"hook-secret-777" not in page.content
