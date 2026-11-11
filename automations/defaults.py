"""Built-in rules every site starts with. New rules stay off until the owner turns them on."""

BUILTIN_RULES = [
    {
        "name": "Forward contact messages to Telegram",
        "trigger": "contact.submitted",
        "action": "telegram.send",
        "is_enabled": True,
        "filters": {},
        "action_config": {"template": "New message from {{name}} <{{email}}>:\n{{message}}"},
    },
    {
        "name": "Alert me when a sync fails",
        "trigger": "sync.failed",
        "action": "telegram.send",
        "is_enabled": True,
        "filters": {},
        "action_config": {"template": "Sync failed: {{provider}} — {{error}}"},
    },
    {
        "name": "Post new releases to the channel",
        "trigger": "github.release.published",
        "action": "telegram.post_channel",
        "is_enabled": False,
        "filters": {},
        "action_config": {"template": "New release {{repo}} {{tag}}\n{{url}}"},
    },
    {
        "name": "Re-sync projects on push to main",
        "trigger": "github.push",
        "action": "site.resync_projects",
        "is_enabled": False,
        "filters": {"branch": "main"},
        "action_config": {},
    },
    {
        "name": "Send contact messages to a webhook",
        "trigger": "contact.submitted",
        "action": "webhook.send",
        "is_enabled": False,
        "filters": {},
        "action_config": {"hook_id": None},
    },
]


def ensure_builtin_rules(rule_model=None):
    """Create any missing built-in rule. Existing ones (and the owner's edits to them) are left alone.

    Migrations pass their historical Rule model; everyone else can call it without arguments.
    """
    if rule_model is None:
        from .models import Rule as rule_model
    created = 0
    for spec in BUILTIN_RULES:
        defaults = {k: v for k, v in spec.items() if k not in ("trigger", "action")}
        _, was_created = rule_model.objects.get_or_create(
            trigger=spec["trigger"], action=spec["action"], is_builtin=True, defaults=defaults
        )
        created += was_created
    return created
