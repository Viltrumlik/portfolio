# ActivityFeed

A log of recent events. Each row has a 24-hour time, a service code, one line of text and optional mono meta, with dashed lines between rows.

**Provide:** `items` (an array of `{ time, datetime, code, source, text, meta, tone }`) and a `label` for the list. `tone: 'danger'` marks a failure and adds the alert glyph.

- **Where.** Put it in a window titled "activity.log". Public pages show a subset of events; the studio shows the full sync log, failures included.
- **Order.** Newest first, with at most ten rows before "Show all".
