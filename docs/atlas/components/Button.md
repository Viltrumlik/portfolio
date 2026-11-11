# Button

A pill-shaped action that lifts onto a hard shadow on hover. It is `secondary` by default, `primary` (a lime fill) once per view, and `ghost` for low-stakes actions.

**Provide:** a verb-first label as `children` ("Connect GitHub", "Sync now"), or an `icon` plus an `aria-label` for an icon-only button. Optional props: `variant`, `size` (`md` is 40px, `sm` is 32px), `icon`, `iconRight`, and `href` to render a link that looks like a button. Any other props go to the `<button>` or `<a>`.

- **Primary.** A `lime` fill with `on-lime` text, outlined by `lime-edge`. Use it for the one thing the view is for.
- **Ghost.** Use it for "Disconnect", "Cancel" and "All projects". Destructive actions are ghost buttons, then confirm in a sentence.
- **Arrows.** `iconRight: 'arrow-up-right'` leaves the site; `'arrow-right'` stays on it.
- **Disabled.** Keep the label and say what's happening ("Syncing…").
