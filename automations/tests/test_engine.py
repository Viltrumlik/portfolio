import pytest

from automations import engine
from automations.events import emit
from automations.models import Event, Rule, RuleRun
from integrations.errors import AuthError, Transient
from integrations.models import Connection, OutboundHook
from integrations.providers import telegram
from integrations.tests.fixtures import body_json
from jobs import registry, runner
from jobs.models import Job

pytestmark = pytest.mark.django_db

TG = "https://api.telegram.org/bot1:tok"


@pytest.fixture(autouse=True)
def only_test_rules():
    Rule.objects.all().delete()


@pytest.fixture
def tg():
    return Connection.objects.create(provider="telegram", status="connected", account="@bot", credentials={"bot_token": "1:tok"}, config={"chat_id": 5, "channel_id": "@news"})


@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(telegram, "send_message", lambda conn, text, chat_id=None: messages.append(("send", text)))
    monkeypatch.setattr(telegram, "post_channel", lambda conn, text: messages.append(("channel", text)))
    return messages


def rule(trigger, action, *, enabled=True, filters=None, **config):
    return Rule.objects.create(name=f"{trigger} to {action}", trigger=trigger, action=action, filters=filters or {}, action_config=config, is_enabled=enabled)


def dispatch(event):
    registry.get("automations.dispatch")({"event_id": event.pk})
    event.refresh_from_db()


# --- templates and filters ------------------------------------------------------------


def test_render_template_substitutes_keys_and_paths():
    payload = {"name": "Ann", "repo": {"name": "atlas"}, "n": 3, "none": None}
    assert engine.render_template("Hi {{name}} {{ repo.name }} {{n}} [{{missing}}] [{{none}}] [{{name.deeper}}]", payload) == "Hi Ann atlas 3 [] [] []"


def test_render_template_escapes_values_only():
    out = engine.render_template("<b>{{name}}</b>", {"name": "<i>x</i>"}, escape=telegram.escape_html)
    assert out == "<b>&lt;i&gt;x&lt;/i&gt;</b>"


def test_render_template_does_not_evaluate_django_template_syntax():
    assert engine.render_template("{% if x %}{{x}}{% endif %}", {"x": "1"}) == "{% if x %}1{% endif %}"


@pytest.mark.parametrize(
    "filters,payload,expected",
    [
        ({}, {"repo": "A1isherDev/atlas"}, True),
        ({"repo": ["atlas"]}, {"repo": "A1isherDev/atlas"}, True),
        ({"repo": ["A1isherDev/atlas"]}, {"repo": "A1isherDev/atlas"}, True),
        ({"repo": ["other"]}, {"repo": "A1isherDev/atlas"}, False),
        ({"repo": "atlas"}, {"repo": "A1isherDev/atlas"}, True),
        ({"repo": ["atlas"]}, {}, False),
        ({"branch": "main"}, {"branch": "main"}, True),
        ({"branch": "main"}, {"branch": "dev"}, False),
        ({"repo": ["atlas"], "branch": "main"}, {"repo": "A1isherDev/atlas", "branch": "dev"}, False),
    ],
)
def test_filters(filters, payload, expected):
    assert engine.matches(filters, payload) is expected


def test_telegram_markup_keeps_supported_tags_and_escapes_the_rest():
    assert telegram.template_markup("<b>New</b> from {{name}} <{{email}}> & co") == "<b>New</b> from {{name}} &lt;{{email}}&gt; &amp; co"


# --- dispatch -------------------------------------------------------------------------


def test_matching_enabled_rule_sends_a_telegram_message(api, tg):
    r = rule("contact.submitted", "telegram.send", template="New message from {{name}} <{{email}}>:\n{{message}}")
    api.add("POST", f"{TG}/sendMessage", json={"ok": True, "result": {}})
    event = Event.objects.create(type="contact.submitted", payload={"name": "Ann", "email": "ann@example.com", "message": "Hi <3"})

    dispatch(event)

    sent = body_json(api.requests[0])
    assert sent["text"] == "New message from Ann &lt;ann@example.com&gt;:\nHi &lt;3"
    assert sent["chat_id"] == 5
    run = RuleRun.objects.get()
    assert (run.rule, run.event, run.status) == (r, event, RuleRun.Status.OK)
    r.refresh_from_db()
    assert r.run_count == 1 and r.last_run_at is not None
    assert event.dispatched_at is not None


def test_post_channel_action(tg, sent):
    rule("github.release.published", "telegram.post_channel", template="New release {{repo}} {{tag}}")
    dispatch(Event.objects.create(type="github.release.published", payload={"repo": "A1isherDev/atlas", "tag": "v1"}))
    assert sent == [("channel", "New release A1isherDev/atlas v1")]


def test_disabled_and_non_matching_rules_do_not_run(tg, sent):
    rule("github.push", "telegram.send", enabled=False, template="x")
    rule("github.push", "telegram.send", filters={"branch": "main"}, template="y")
    rule("contact.submitted", "telegram.send", template="z")
    dispatch(Event.objects.create(type="github.push", payload={"repo": "a/b", "branch": "dev"}))
    assert sent == []
    assert not RuleRun.objects.exists()


def test_failed_action_is_recorded_and_other_rules_still_run(tg, sent, monkeypatch):
    def broken(conn, text):
        raise Transient("Telegram is having trouble (502). It will retry.")

    monkeypatch.setattr(telegram, "post_channel", broken)
    first = rule("contact.submitted", "telegram.post_channel", template="a")
    second = rule("contact.submitted", "telegram.send", template="b")
    dispatch(Event.objects.create(type="contact.submitted"))
    assert RuleRun.objects.get(rule=first).status == RuleRun.Status.FAILED
    assert "502" in RuleRun.objects.get(rule=first).output
    assert RuleRun.objects.get(rule=second).status == RuleRun.Status.OK
    assert sent == [("send", "b")]
    first.refresh_from_db()
    assert first.run_count == 1


def test_rejected_bot_token_flags_telegram_and_reports_once(tg, monkeypatch):
    def rejected(conn, text, chat_id=None):
        raise AuthError("Telegram rejected the bot token.", code="401")

    monkeypatch.setattr(telegram, "send_message", rejected)
    rule("contact.submitted", "telegram.send", template="a")
    rule("sync.failed", "telegram.send", template="Sync failed: {{provider}} — {{error}}")

    dispatch(Event.objects.create(type="contact.submitted"))
    tg.refresh_from_db()
    assert tg.status == Connection.Status.ERROR
    failed = Event.objects.get(type="sync.failed")
    assert failed.payload == {"provider": "telegram", "error": "Telegram rejected the bot token."}

    dispatch(failed)  # the sync.failed alert also fails: no further sync.failed
    assert Event.objects.filter(type="sync.failed").count() == 1


def test_telegram_rules_are_skipped_when_telegram_is_not_connected(sent):
    r = rule("contact.submitted", "telegram.send", template="a")
    dispatch(Event.objects.create(type="contact.submitted"))
    run = RuleRun.objects.get()
    assert run.status == RuleRun.Status.SKIPPED
    assert not Event.objects.filter(type="sync.failed").exists()
    r.refresh_from_db()
    assert r.run_count == 0


def test_webhook_send_queues_a_signed_delivery():
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/h", secret={"secret": "s"})
    rule("contact.submitted", "webhook.send", hook_id=hook.pk)
    event = Event.objects.create(type="contact.submitted")
    dispatch(event)
    job = Job.objects.get(kind="webhook.deliver")
    assert job.payload == {"hook_id": hook.pk, "event_id": event.pk}
    assert RuleRun.objects.get().status == RuleRun.Status.OK


def test_webhook_send_to_a_missing_hook_fails():
    rule("contact.submitted", "webhook.send", hook_id=None)
    dispatch(Event.objects.create(type="contact.submitted"))
    assert RuleRun.objects.get().status == RuleRun.Status.FAILED


def test_resync_projects_queues_a_github_sync():
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    rule("github.push", "site.resync_projects", filters={"branch": "main"})
    event = Event.objects.create(type="github.push", payload={"repo": "a/b", "branch": "main"})
    dispatch(event)
    job = Job.objects.get(kind="github.sync")
    assert job.payload == {"trigger": "github.push", "event_id": event.pk}
    assert RuleRun.objects.get().status == RuleRun.Status.OK


def test_outbound_hooks_get_the_event_types_they_subscribe_to():
    wanted = OutboundHook.objects.create(name="a", url="https://a.example.com/", events=["contact.submitted"])
    OutboundHook.objects.create(name="b", url="https://b.example.com/", events=["github.push"])
    OutboundHook.objects.create(name="c", url="https://c.example.com/", events=["contact.submitted"], is_active=False)
    event = Event.objects.create(type="contact.submitted")
    dispatch(event)
    assert list(Job.objects.filter(kind="webhook.deliver").values_list("payload", flat=True)) == [{"hook_id": wanted.pk, "event_id": event.pk}]


def test_an_event_is_dispatched_once(tg, sent):
    rule("contact.submitted", "telegram.send", template="a")
    event = Event.objects.create(type="contact.submitted")
    dispatch(event)
    dispatch(event)
    assert len(sent) == 1


def test_missing_event_is_ignored():
    registry.get("automations.dispatch")({"event_id": 999999})


def test_emit_then_run_jobs_runs_the_rule_end_to_end(tg, sent):
    rule("contact.submitted", "telegram.send", template="From {{name}}")
    emit("contact.submitted", {"name": "Ann"})
    runner.run_due(10)
    assert sent == [("send", "From Ann")]
