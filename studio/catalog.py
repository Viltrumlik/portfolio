"""What the studio knows about services, events and actions: codes, labels and the copy from docs/atlas/integrations.md."""
from automations.models import Rule

PROVIDERS = {
    "github": {
        "name": "GitHub",
        "code": "GH",
        "feeds": "Repos, pinned projects, the contribution graph, and push and release events.",
        "cadence": "hourly + push",
        "secret_label": "Token",
        "disconnect": "Disconnect GitHub? Projects stay on the site but stop updating.",
    },
    "telegram": {
        "name": "Telegram",
        "code": "TG",
        "feeds": "Forwards contact-form messages to me and posts to my channel.",
        "cadence": "sends as events happen",
        "secret_label": "Bot token",
        "disconnect": "Disconnect Telegram? Contact messages stay in the inbox but stop arriving in Telegram.",
    },
    "lastfm": {
        "name": "Last.fm",
        "code": "LF",
        "feeds": "The track playing now, for the now.app window.",
        "cadence": "every minute",
        "secret_label": "API key",
        "disconnect": "Disconnect Last.fm? The now-playing track leaves the site.",
    },
}

# Event types rules and webhooks can react to: (type, short label, service code, service name).
EVENTS = [
    ("github.push", "Pushed to a repo", "GH", "GitHub"),
    ("github.release.published", "New release published", "GH", "GitHub"),
    ("contact.submitted", "Contact message received", "ST", "This site"),
    ("post.published", "Post published", "ST", "This site"),
    ("sync.failed", "A sync failed", "ST", "This site"),
]
EVENT_TYPES = [(key, label) for key, label, _, _ in EVENTS]
EVENT_INFO = {key: {"label": label, "code": code, "service": service} for key, label, code, service in EVENTS}

# A realistic payload per trigger, for the template preview.
SAMPLES = {
    "github.push": {"repo": "A1isherDev/volunteers_bot", "branch": "main", "commits": 3,
                    "url": "https://github.com/A1isherDev/volunteers_bot/compare/1a2b3c...4d5e6f", "head": "4d5e6f"},
    "github.release.published": {"repo": "A1isherDev/volunteers_bot", "tag": "v1.4.0", "name": "v1.4.0",
                                 "url": "https://github.com/A1isherDev/volunteers_bot/releases/tag/v1.4.0"},
    "contact.submitted": {"id": 42, "name": "Dilnoza", "email": "dilnoza@example.com",
                          "message": "Could you build a booking bot for our clinic?"},
    "post.published": {"title": "Notes from building things", "url": "https://guts.uz/writing/notes-from-building-things/"},
    "sync.failed": {"provider": "lastfm", "error": "Last.fm rejected the API key (error 10). Paste a new key to resume syncing."},
}

ACTIONS = {
    Rule.Action.TELEGRAM_SEND: {"label": "Message me on Telegram", "code": "TG", "service": "Telegram", "slug": "telegram"},
    Rule.Action.TELEGRAM_POST: {"label": "Post to channel", "code": "TG", "service": "Telegram", "slug": "channel"},
    Rule.Action.WEBHOOK_SEND: {"label": "Send to a webhook", "code": "WH", "service": "Outgoing webhook", "slug": "webhook"},
    Rule.Action.RESYNC: {"label": "Re-sync projects", "code": "ST", "service": "This site", "slug": "resync"},
}
TEMPLATE_ACTIONS = {Rule.Action.TELEGRAM_SEND, Rule.Action.TELEGRAM_POST}

TRIGGER_SLUGS = {
    "github.push": "push",
    "github.release.published": "release",
    "contact.submitted": "contact",
    "post.published": "post",
    "sync.failed": "sync-failed",
}

SOURCE_CODES = {"github": "GH", "lastfm": "LF", "telegram": "TG", "webhook": "WH", "wakatime": "WK", "site": "ST", "automations": "ST"}
CODE_NAMES = {"GH": "GitHub", "LF": "Last.fm", "TG": "Telegram", "WH": "Outgoing webhook", "WK": "WakaTime", "ST": "This site"}
