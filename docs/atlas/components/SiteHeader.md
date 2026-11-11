# SiteHeader

The menu bar across the top: a lime square and the site name, primary links, live availability, the owner's local time, and a ⌘K button.

**Provide:**
- `name` (e.g. "alisher.os").
- `links`: an array of `{ label, href, active }`, five at most.
- `status`: optional `{ label, pulse }`.
- `city` and `timeZone`, to show a ticking HH:MM clock.
- `onCommand`, to open the `CommandPalette`.
- `homeHref`.

- **Active link.** Mark one link active. It gets a 2px `signal` underline and `aria-current="page"`.
- **Phones.** Under 720px the links and status hide, so ⌘K must list every page.
- **Status.** Keep it honest: change it from the studio, or leave it out.
