import pytest

from automations.defaults import ensure_builtin_rules
from automations.models import Rule

pytestmark = pytest.mark.django_db

EXPECTED = {
    ("contact.submitted", "telegram.send"): (True, {}, "New message from {{name}} <{{email}}>:\n{{message}}"),
    ("sync.failed", "telegram.send"): (True, {}, "Sync failed: {{provider}} — {{error}}"),
    ("github.release.published", "telegram.post_channel"): (False, {}, "New release {{repo}} {{tag}}\n{{url}}"),
    ("github.push", "site.resync_projects"): (False, {"branch": "main"}, None),
    ("contact.submitted", "webhook.send"): (False, {}, None),
}


def builtins():
    return {
        (r.trigger, r.action): (r.is_enabled, r.filters, r.action_config.get("template"))
        for r in Rule.objects.filter(is_builtin=True)
    }


def test_the_migration_installs_the_builtin_rules():
    assert builtins() == EXPECTED


def test_ensure_builtin_rules_is_idempotent_and_keeps_owner_edits():
    Rule.objects.filter(trigger="sync.failed").update(is_enabled=False, action_config={"template": "Mine"})
    ensure_builtin_rules()
    ensure_builtin_rules()
    assert Rule.objects.filter(is_builtin=True).count() == 5
    edited = Rule.objects.get(trigger="sync.failed")
    assert (edited.is_enabled, edited.action_config) == (False, {"template": "Mine"})


def test_ensure_builtin_rules_restores_a_deleted_rule():
    Rule.objects.filter(trigger="github.push").delete()
    ensure_builtin_rules()
    assert builtins() == EXPECTED


def test_builtin_rules_have_names():
    assert all(r.name for r in Rule.objects.filter(is_builtin=True))
