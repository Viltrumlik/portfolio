# SiteHeader

The sticky menu bar across the top: the site name in glowing VT323 with a blinking block cursor after it, `/`-prefixed links, live availability, the owner's local time, and a ⌘K button. On the site it also carries the sound toggle.

**Provide:**
- `name` (e.g. "alisher.os").
- `links`: an array of `{ label, href, active }`, five at most.
- `status`: optional `{ label, pulse }`.
- `city` and `timeZone`, to show a ticking HH:MM clock.
- `onCommand`, to open the `CommandPalette`.
- `homeHref`.

- **Active link.** Mark one link active. It turns `signal`, its `/` becomes `>`, and it gets `aria-current="page"`.
- **Phones.** Under 720px the links and status hide, so ⌘K must list every page.
- **Status.** Keep it honest: change it from the studio, or leave it out.
