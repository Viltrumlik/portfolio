import pytest

from automations.models import Event
from integrations import handlers  # noqa: F401  (registered on app start)
from integrations.models import Connection, OutboundHook
from integrations.providers import github, lastfm, telegram, webhook
from jobs import registry, runner
from jobs.models import Job
from jobs.queue import enqueue

pytestmark = pytest.mark.django_db


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def record(name, result=None):
        def fake(*args, **kwargs):
            seen.append((name, args, kwargs))
            return result

        return fake

    monkeypatch.setattr(github, "full_sync", record("full_sync"))
    monkeypatch.setattr(github, "poll_events", record("poll_events"))
    monkeypatch.setattr(lastfm, "poll", record("lastfm.poll"))
    monkeypatch.setattr(webhook, "deliver", record("deliver"))
    return seen


def test_provider_kinds_are_registered():
    for kind in ["github.sync", "github.events", "lastfm.poll", "telegram.sync", "webhook.deliver"]:
        assert registry.get(kind) is not None, kind


def test_github_jobs_call_the_provider_for_a_live_connection(calls):
    conn = Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    registry.get("github.sync")({})
    registry.get("github.events")({})
    assert [(name, args[0].pk) for name, args, _ in calls] == [("full_sync", conn.pk), ("poll_events", conn.pk)]


def test_provider_jobs_do_nothing_when_disconnected(calls):
    Connection.objects.create(provider="github", status="off", credentials={})
    registry.get("github.sync")({})
    registry.get("lastfm.poll")({})
    registry.get("telegram.sync")({})
    assert calls == []


def test_lastfm_job_polls(calls):
    Connection.objects.create(provider="lastfm", status="connected", credentials={"api_key": "k"})
    registry.get("lastfm.poll")({})
    assert calls[0][0] == "lastfm.poll"


def test_webhook_deliver_job_sends_to_an_active_hook(calls):
    hook = OutboundHook.objects.create(name="n8n", url="https://x.example.com/", secret={"secret": "s"})
    event = Event.objects.create(type="contact.submitted")
    registry.get("webhook.deliver")({"hook_id": hook.pk, "event_id": event.pk})
    assert calls[0][0] == "deliver"
    assert (calls[0][1][0].pk, calls[0][1][1].pk) == (hook.pk, event.pk)


def test_webhook_deliver_job_skips_inactive_or_missing_hooks(calls):
    hook = OutboundHook.objects.create(name="off", url="https://x.example.com/", is_active=False)
    event = Event.objects.create(type="contact.submitted")
    registry.get("webhook.deliver")({"hook_id": hook.pk, "event_id": event.pk})
    registry.get("webhook.deliver")({"hook_id": 999, "event_id": event.pk})
    assert calls == []


def test_telegram_sync_refreshes_the_bot_and_finds_the_chat(monkeypatch):
    conn = Connection.objects.create(provider="telegram", status="syncing", credentials={"bot_token": "1:x"}, config={"channel_id": "@c"})
    monkeypatch.setattr(telegram, "verify", lambda token: {"id": 1, "username": "atlas_bot"})
    monkeypatch.setattr(telegram, "find_chat_id", lambda token: 4242)
    registry.get("telegram.sync")({})
    conn.refresh_from_db()
    assert conn.status == Connection.Status.CONNECTED
    assert conn.account == "@atlas_bot"
    assert conn.config == {"channel_id": "@c", "chat_id": 4242}


def test_a_rejected_github_token_flags_the_connection_end_to_end(api):
    Connection.objects.create(provider="github", status="connected", account="A1isherDev", credentials={"token": "bad"})
    api.add("POST", "https://api.github.com/graphql", status=401, json={})
    job = enqueue("github.sync")
    runner.run_due(10)
    job.refresh_from_db()
    assert job.status == Job.Status.FAILED
    conn = Connection.objects.get(provider="github")
    assert conn.status == Connection.Status.ERROR
    assert "GitHub rejected the token" in conn.last_error
    assert Event.objects.get(type="sync.failed").payload["provider"] == "github"
