# Stat

A single number with its label, set in Martian Mono with tabular figures over an `edge` hairline.

**Provide:** `value` (a formatted string) and `label`. Optional: `unit`, `delta` and `trend: 'down'`.

- Only show numbers that come from a connected source and update on their own.
- A rising `delta` is `signal`. A falling one stays `ink-muted`, because down isn't an error.
- Put two to four inside a window. One alone is fine only in a small widget window.
