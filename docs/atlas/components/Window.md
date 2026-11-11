# Window

The basic Atlas container: a title bar with three controls and a mono file name, over a padded body. It sits on a hard offset shadow and lifts on hover.

**Provide:** `title` (a lowercase file name, such as "about.md", "github.app" or "connections/github") and `children`. Optional props:
- `active`: gives the title bar a lime fill. Only one window per screen is active.
- `barEnd`: content at the right end of the title bar, such as a `Kbd` or a `Switch`.
- `label`: the accessible name, if it should differ from `title`.
- `role`, `className`, `style`, and `id` (used by `Desktop`).

- Every block of reading content lives in a window. The desk itself only carries windows, the dock and notes.
- A window is a `<section>` named by its title, so screen readers can jump between windows.
- `NowCard`, `IntegrationCard`, `AutomationRule` and `CommandPalette` are windows already. Don't wrap them in another one.
