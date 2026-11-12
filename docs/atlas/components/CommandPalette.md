# CommandPalette

The ⌘K window: one search field over grouped pages, projects and actions, driven entirely from the keyboard.

**Provide:**
- `groups`: an array of `{ label, items: [{ label, hint, icon, shortcut, keywords }] }`.
- `onSelect(item)` and `onClose`.
- Optional: `title`, `placeholder` and `autoFocus`.

Center it over a dimmed desk when it opens from `SiteHeader`.

- **Keys.** ↑/↓ move, ↵ opens and esc closes. Search matches the label, hint and `keywords`.
- **Group order.** Pages, Projects, Writing, Actions. Group labels read `// PAGES`; the selected row gets `signal-soft` and a 2px `signal` rule on the left.
- **Theme switch.** "Switch theme" is always in Actions. It cycles green → amber → ice.
- **Owner-only actions** ("Open studio") appear only when the owner is signed in.
