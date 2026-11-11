# Dock

A row of service stamps in a floating window frame at the bottom of the desk. Items spring up when hovered.

**Provide:** `items` as an array of `{ code, label, href | onClick, active }`, plus an optional `label` for the nav.

- Use it for quick jumps: open a connection's window, scroll to a section, or start an email.
- One item at most is `active` (lime).
- Seven items at most.
- Inside `Desktop` it is pinned to the bottom center. On phones it sticks to the bottom of the stack.
