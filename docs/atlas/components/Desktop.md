# Desktop

The hero canvas: a dotted desk with windows placed on it, which visitors can drag by their title bars.

**Provide:** `items` as an array of `{ id, title, x, y, w, content, label }`:
- `x` and `w`: CSS lengths, usually percentages ("3%", "46%").
- `y`: pixels.
- `content`: the window body.

Optional: `height` (default 520), `activeId`, and `children` (usually a `Dock`).

- **Load.** Windows pop in one after another, 100ms apart. Pressing a title bar brings that window to the front, makes it active and lets it be dragged inside the desk.
- **Small screens.** Under 720px the desk becomes a vertical stack in DOM order, and dragging is off.
- **Order.** Put items in reading order: dragging is a bonus, and the DOM order is what keyboards and screen readers get.
- **Placement.** Set windows on the 12-column grid: the hero window across about 6 columns, widgets in the rest.
