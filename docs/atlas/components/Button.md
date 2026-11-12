# Button

A bracketed terminal command: CSS uppercases the label and draws `[ ]` around it. It is `secondary` by default (an outline with glowing `signal` text that fills with `signal` on hover), `primary` (a glowing `lime` fill) once per view, and `ghost` (no brackets, no outline) for low-stakes actions.

**Provide:** a verb-first label as `children` ("Connect GitHub", "Sync now"), or an `icon` plus an `aria-label` for an icon-only button. Optional props: `variant`, `size` (`md` is 38px, `sm` is 30px), `icon`, `iconRight`, and `href` to render a link that looks like a button. Any other props go to the `<button>` or `<a>`.

- **Primary.** A `lime` fill with `on-lime` text, outlined by `lime-edge`, blooming with `glow-strong`. It turns `phosphor-hot` on hover. Use it for the one thing the view is for.
- **Ghost.** Use it for "Disconnect", "Cancel" and "All projects". Destructive actions are ghost buttons, then confirm in a sentence.
- **Arrows.** `iconRight: 'arrow-up-right'` leaves the site; `'arrow-right'` stays on it.
- **Disabled.** Keep the label and say what's happening ("Syncing…"). Don't type brackets or capitals into the label.
