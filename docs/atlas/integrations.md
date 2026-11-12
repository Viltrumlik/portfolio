# Connections and automation

The site gets its live content from services the owner connects, and runs small automations when things happen. These screens live in an owner-only studio (`/studio/connections` and `/studio/automations`). They use the same desk and windows as the public site.

## Service codes

Every service appears as a two-letter `ServiceCode` or dock item, never as a brand logo.

| Code | Service | What it feeds |
|---|---|---|
| GH | GitHub | Repos, pinned projects, the contribution graph, push and release events |
| WK | WakaTime | Coding time and languages for the `NowCard` and stats |
| LF | Last.fm | The track playing now, for the `NowCard` |
| TG | Telegram | Forwarded contact-form messages and channel posts |
| WH | Outgoing webhook | Signed events sent to n8n, Make or Zapier |
| RS | RSS | The blog feed, in and out |
| ST | This site | Internal jobs such as re-syncing projects and rebuilding OG images |

To add a service, pick an unused two-letter code and add a row here.

## Connection states

Each `IntegrationCard` is a window titled "connections/<name>", and it is in exactly one state. The badge always carries a word, never color alone.

| State | Badge | Actions | Copy |
|---|---|---|---|
| `off` | neutral "Not connected" | primary "Connect" | One sentence on what the service feeds |
| `syncing` | accent "Syncing", blinking dot | disabled "Syncing…", ghost "Disconnect" | The cadence ("Daily at 03:00") |
| `connected` | live "Connected" | "Sync now", ghost "Disconnect" | The last sync and the cadence ("4 min ago · hourly + push") |
| `error` | danger "Needs attention" with the alert glyph; the window's outline and title bar turn `danger` | primary "Reconnect", ghost "Disconnect" | What failed, the service's error code and the next step |

- **Secrets.** Show account handles (`@A1isherDev`) and masked keys (`API key •••• 91ab`). Never show a full token, not even to the owner.
- **Access.** List the granted scopes in the service's own terms (`read:user`, `public_repo`).
- **Disconnect.** It is a ghost button, and asks once in a sentence: "Disconnect GitHub? Projects stay on the site but stop updating."

## Automation rules

A rule is one trigger and one action, read as a sentence: **When** something happens in a service, **then** do something in another. Use `AutomationRule`, a window titled "rules/<trigger>-to-<action>".

- Labels are short verb phrases ("New release published", "Post to channel"). Details are in mono and name the filter or the payload ("any public repo", "signed POST · HMAC-SHA256").
- The switch turns a rule off without deleting it. A new rule stays off until the owner has seen it run once.
- The footer counts runs and says when the last one happened ("14 runs · last 3 days ago").

## Sync log

Show the log with `ActivityFeed` in a window titled "activity.log". Each row has a 24-hour time, the service code, one line saying what happened, and optional mono meta.

Mark failures with `tone: 'danger'`, which adds the alert glyph. Keep failed rows in the log.

## The studio desk

The studio reuses `Desktop`. On load:
- The connections are windows in a grid.
- The sync log is a tall window on the right.
- The dock holds one item per connected service.

An item opens and activates its connection's window.

## Public surfaces

Visitors only ever see cached data, never a live call to a service:
- `ContributionGraph` and `RepoCard` show GitHub data.
- `NowCard` shows the local time, WakaTime and Last.fm.
- `ActivityFeed` shows a public subset of the log.

When a service is disconnected, hide its window and its dock item. Don't show zeros in their place.
