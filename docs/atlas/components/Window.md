# Window

The basic Atlas container: a terminal window whose title bar reads `■ TITLE ……… [_][□][x]`, over a padded body. It sits in a phosphor bloom (`shadow-hard`), blooms brighter on hover and its bar jitters once.

**Provide:** `title` (a lowercase file name, such as "about.sys", "stack.cfg" or "connections/github"; CSS uppercases it) and `children`. Optional props:
- `active`: gives the title bar a glowing `lime` fill. Only one window per screen is active.
- `barEnd`: content at the right end of the title bar, such as a `Kbd` or a `Switch`.
- `label`: the accessible name, if it should differ from `title`.
- `role`, `className`, `style`, and `id` (used by `Desktop`).

- Every block of reading content lives in a window. The desk itself only carries windows and the dock.
- A window is a `<section>` named by its title, so screen readers can jump between windows.
- `NowCard`, `IntegrationCard`, `AutomationRule` and `CommandPalette` are windows already. Don't wrap them in another one.
