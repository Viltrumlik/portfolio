# NowCard

A live "now" window. It shows the owner's local time ticking each second, availability, and what's being coded and played.

**Provide:**
- `timeZone`: an IANA zone. The default is `Asia/Tashkent`.
- `location` and `utc`.
- Optional: `status`, `coding` (`{ project, detail }`), `listening` (`{ track, artist }`), `title` (default "now.app") and `active`.

- **Rows.** Each row appears only when its source is connected. "Nothing playing" is a fine state; a fake track is not.
- **Placement.** It already is a window, so place it straight on the desk or the page grid.
