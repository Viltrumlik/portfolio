# Desktop

The hero canvas: a transparent desk (the digital rain shows through) with windows placed on it, which visitors can drag by their title bars.

**Provide:** `items` as an array of `{ id, title, x, y, w, content, label }`:
- `x` and `w`: CSS lengths, usually percentages ("3%", "46%").
- `y`: pixels.
- `content`: the window body.

Optional: `height` (default 520), `activeId`, and `children` (usually a `Dock`).

- **Load.** Windows switch on like a CRT, one after another: from a thin, overbright line to full height. Pressing a title bar brings that window to the front, makes it active and lets it be dragged inside the desk.
- **Small screens.** Under 720px the desk becomes a vertical stack in DOM order, and dragging is off. The site stacks it under 1024px.
- **Order.** Put items in reading order: dragging is a bonus, and the DOM order is what keyboards and screen readers get.
- **Placement.** The site packs nine windows into three columns (37%, 33% and 23% wide) with 20px gaps, and leaves out any window with nothing to show so the rest move up (`web/desk.py`).
