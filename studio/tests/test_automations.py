"""Automation rules: list as AutomationRule windows, toggle, create/edit with a template preview, delete."""
import json
import re

import pytest
from django.utils import timezone

from automations.models import Event, Rule, RuleRun
from integrations.models import OutboundHook

pytestmark = pytest.mark.django_db


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


def builtin(trigger, action):
    return Rule.objects.get(trigger=trigger, action=action, is_builtin=True)


def test_list_shows_rules_as_sentences_with_switches(staff):
    rule = builtin("github.release.published", "telegram.post_channel")
    Rule.objects.filter(pk=rule.pk).update(run_count=14, last_run_at=timezone.now() - timezone.timedelta(days=3))
    page = html(staff.get("/studio/automations/"))
    assert '<span class="at-win__title">rules/release-to-channel</span>' in page
    assert '<span class="at-rule__word">When</span>' in page and '<span class="at-rule__word">Then</span>' in page
    assert '<div class="at-rule__label">New release published</div>' in page
    assert '<div class="at-rule__label">Post to channel</div>' in page
    assert "14 runs · last 3 days ago" in page
    assert 'role="switch" aria-checked="false" class="at-switch"' in page
    assert 'role="switch" aria-checked="true" class="at-switch is-on"' in page  # the contact → Telegram rule is on
    assert 'href="/studio/webhooks/"' in page


def test_toggle_turns_a_rule_on_and_off(staff):
    rule = builtin("github.push", "site.resync_projects")
    r = staff.post(f"/studio/automations/{rule.pk}/toggle/", {"enabled": "1"})
    assert r.status_code == 302 and r["Location"] == "/studio/automations/"
    rule.refresh_from_db()
    assert rule.is_enabled is True
    staff.post(f"/studio/automations/{rule.pk}/toggle/", {"enabled": "0"})
    rule.refresh_from_db()
    assert rule.is_enabled is False


def test_new_rule_form_has_triggers_actions_and_the_template_preview(staff):
    page = html(staff.get("/studio/automations/new/"))
    for event in ("github.push", "github.release.published", "contact.submitted", "post.published", "sync.failed"):
        assert f'<option value="{event}"' in page
    for action in ("telegram.send", "telegram.post_channel", "webhook.send", "site.resync_projects"):
        assert f'<option value="{action}"' in page
    match = re.search(r'data-island="template-preview" data-sample="([^"]*)"', page)
    assert match
    sample = json.loads(match.group(1).replace("&quot;", '"'))
    assert sample["repo"]
    assert "data-template-input" in page and "data-template-output" in page


def test_create_a_rule_starts_off(staff):
    r = staff.post("/studio/automations/new/", {
        "name": "Tell me about releases", "trigger": "github.release.published", "repo": "volunteers_bot, pul-olami",
        "branch": "", "action": "telegram.send", "template": "New release {{repo}} {{tag}}",
    })
    assert r.status_code == 302
    rule = Rule.objects.get(name="Tell me about releases")
    assert r["Location"] == f"/studio/automations/{rule.pk}/"
    assert (rule.is_enabled, rule.is_builtin) == (False, False)
    assert rule.filters == {"repo": ["volunteers_bot", "pul-olami"]}
    assert rule.action_config == {"template": "New release {{repo}} {{tag}}"}


def test_create_a_webhook_rule_needs_a_webhook(staff):
    page = html(staff.post("/studio/automations/new/", {"name": "Hook", "trigger": "post.published", "action": "webhook.send"}))
    assert "Pick a webhook for this rule." in page
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/h", secret={"secret": "s"})
    r = staff.post("/studio/automations/new/", {"name": "Hook", "trigger": "post.published", "action": "webhook.send", "hook": hook.pk, "branch": "main"})
    assert r.status_code == 302
    rule = Rule.objects.get(name="Hook")
    assert rule.action_config == {"hook_id": hook.pk}
    assert rule.filters == {"branch": "main"}


def test_telegram_rules_need_a_message(staff):
    page = html(staff.post("/studio/automations/new/", {"name": "Empty", "trigger": "post.published", "action": "telegram.send", "template": " "}))
    assert "Write the message to send." in page
    assert not Rule.objects.filter(name="Empty").exists()


def test_unknown_trigger_is_rejected(staff):
    page = html(staff.post("/studio/automations/new/", {"name": "X", "trigger": "user.deleted", "action": "site.resync_projects"}))
    assert "Select a valid choice" in page


def test_edit_page_shows_recent_runs_and_the_trigger_sample(staff):
    rule = builtin("contact.submitted", "telegram.send")
    RuleRun.objects.create(rule=rule, event=Event.objects.create(type="contact.submitted"), status="ok", output="Sent a Telegram message.")
    page = html(staff.get(f"/studio/automations/{rule.pk}/"))
    assert "Sent a Telegram message." in page
    assert "dilnoza@example.com" in page  # the contact.submitted sample feeds the preview
    assert "New message from {{name}}" in page


def test_builtin_rules_keep_their_trigger_and_action(staff):
    rule = builtin("contact.submitted", "telegram.send")
    r = staff.post(f"/studio/automations/{rule.pk}/", {
        "name": "Forward it", "trigger": "github.push", "action": "site.resync_projects", "template": "From {{name}}",
    })
    assert r.status_code == 302
    rule.refresh_from_db()
    assert (rule.name, rule.trigger, rule.action) == ("Forward it", "contact.submitted", "telegram.send")
    assert rule.action_config == {"template": "From {{name}}"}


def test_delete_a_custom_rule(staff):
    rule = Rule.objects.create(name="Mine", trigger="post.published", action="telegram.send", action_config={"template": "x"})
    r = staff.post(f"/studio/automations/{rule.pk}/delete/")
    assert r.status_code == 302 and r["Location"] == "/studio/automations/"
    assert not Rule.objects.filter(pk=rule.pk).exists()


def test_builtin_rules_cannot_be_deleted(staff):
    rule = builtin("sync.failed", "telegram.send")
    assert staff.post(f"/studio/automations/{rule.pk}/delete/").status_code == 403
    assert Rule.objects.filter(pk=rule.pk).exists()
    assert "Delete rule" not in html(staff.get(f"/studio/automations/{rule.pk}/"))
