Atlas is the design system for a backend developer's portfolio that runs like a small operating system. The home page is a dotted desk with windows you can drag: an about window, a live GitHub graph, coding time, what's playing. A menu bar runs across the top and a dock across the bottom. The windows have hard offset shadows, the type is bold, and there is one electric-lime signal. Everything on the desk is real data from connected services (GitHub, WakaTime, Last.fm, Telegram).

## Principles

- **A desktop, not a document.** The hero is a `Desktop` of `Window`s under a `SiteHeader` menu bar, with a `Dock` at the bottom. Below it, pages scroll normally, but content still lives in windows.
- **Data is the ornament.** Every window shows something true and current: the contribution graph, coding time, the local clock, the sync log. If a source isn't connected, leave its window out. Never show fake data.
- **Hard edges.** Use solid fills, outlines and hard offset shadows (`shadow-hard`, `shadow-lift`). No blur, glass, gradients or glows.
- **One signal.** `lime` is the only accent color. It fills the active title bar, the primary button, live dots, notes and the active dock item. Only one window on screen is active.
- **Motion with a job.** Windows pop in, lift when hovered and tilt while dragged. Dock icons spring up. Live dots ping. Nothing moves just to decorate.

## Content fundamentals

- Write in the first person singular, plainly and specifically: "I build server-side systems, REST APIs and bots that keep working after launch." Avoid vague self-praise.
- Use sentence case for titles, buttons and nav. Capitals appear only in `mono-caps` labels, which CSS uppercases.
- Title windows like files, in lowercase: "about.md", "github.app", "now.app", "activity.log", "connections/github". It's the one place the system plays along with its metaphor.
- Small asides are welcome in notes ("psst: drag the windows"), at most one per screen.
- Start each button with a verb and name its object: "Sync now", "Download CV", "Reconnect Last.fm".
- No emoji, in copy or as icons.
- **Numbers and times.**
  - Write numbers as numerals with units: "4h 12m", "14 repos", "99.6%".
  - Use 24-hour times in the owner's zone (UTC+5): "14:02".
  - Under an hour, use relative time: "4 min ago".
- An error says what failed, why, and what to do next: "Last.fm rejected the API key (error 10). Paste a new key to resume syncing."
- UI copy is English. Project names keep their own language ("Pul Olami"). Uzbek text uses ʻ (U+02BB) in oʻ and gʻ.

## Color

There are two themes:
- **Pulse** (dark) is the default.
- **Sage** (light) has a sage-green desk with cream windows outlined in ink.

Follow `prefers-color-scheme` only once a visitor has chosen; until then, show Pulse. Visitors can switch from ⌘K, and the choice is remembered.

- **Surfaces.**
  - `desk`: the ground, with the `desk-dot` grid at `desk-pitch` (18px).
  - `window`: windows, inputs and the dock.
  - `window-bar`: inactive title bars and the menu bar.
  - `well`: kbd keys, service codes, dock items and empty cells.
- **Text.**
  - `ink` for reading text and `ink-muted` for metadata. Both pass 4.5:1 on every surface in both themes.
  - Only `ink` and `ink-muted` sit directly on the desk.
- **Lines.**
  - `edge`: window outlines and the rules inside windows. Quiet in Pulse, a bold ink outline in Sage.
  - `edge-strong`: wherever the border shows that something is a control.
- **Accent.**
  - `lime` is a fill only. Use `on-lime` text on it and `lime-edge` as its outline.
  - When the accent is text or a mark inside a window, use `signal`. It is lime in Pulse and darkens to olive in Sage, because lime text on cream is unreadable (1.2:1).
  - `signal-soft` is the tint behind `signal` text.
- **State.**
  - `danger` means failed, invalid or expired, and always comes with the alert glyph and a sentence.
  - In Sage, `signal` and `danger` have similar lightness, so the words and glyphs carry the meaning, never the color alone.
- **Data.** `heat-0` to `heat-4` are a lime ramp. Use them only in the contribution graph and on the cover.

## Type

- **`sans` (Bricolage Grotesque).** It carries the voice and the reading text: `display-xl`, `display-lg`, `headline`, `title`, `body-lg`, `body`, `body-sm` and `label`. Display sizes are bold and tightly tracked. Its optical-size axis keeps small text open, so leave `font-optical-sizing` on auto.
- **`mono` (Martian Mono)** is for anything a machine produced:
  - `mono`: code, timestamps, repo names.
  - `mono-sm`: window titles, the menu bar, dock codes, kbd keys.
  - `mono-caps`: ledger keys, section indexes.
  - `numeral`: stats and the clock.

  Martian runs wide, so keep it at 12px or smaller in running UI. Numbers use tabular figures.
- Use one `display-xl` line per page, inside the about window. Keep running text within `measure` (64ch).
- Both families load from Google Fonts through the `@import` at the top of `components/bundle.css`.

## Layout

- **Desktop hero.**
  - The `SiteHeader` menu bar sits at the top, and a `Desktop` takes most of the first screen.
  - Place windows on a 12-column grid: the about window across about 6 columns, widget windows (`github.app`, `wakatime`, `now-playing`) in the other 6.
  - The `Dock` is centered at the bottom.
- **Below the desktop.** Sections scroll as usual inside `container-max` (1240px). Each section is a window opened by a `SectionHeader`. Project lists are `ProjectRow`s in a window; repos are a grid of `RepoCard`s.
- **Phones (under 720px).**
  - The desk becomes a vertical stack of windows in reading order. Dragging is off, the dock sticks to the bottom, and the menu bar keeps only the name, clock and ⌘K.
  - Page gutters are `space-5`.
- **Spacing.** The base unit is 4px, from `space-1` to `space-10`. Window bodies use `space-4`, gaps between windows `space-5`, and top-level sections are `space-9` apart.

## Windows, borders, radii and shadows

- **Anatomy.** A window has a 30px title bar with three outlined controls and a `mono-sm` title, then a body padded by `space-4`. It has a 1.5px `edge` outline, `radius-md` corners and `shadow-hard`.
- **Active.** The title bar fills with `lime`. Only one window on screen is active: the one most recently touched, or the about window on load.
- **Hover and drag.** On hover the window moves 3px up and left and takes `shadow-lift`; in Pulse its outline also turns lime. While dragged, it also tilts -0.6°.
- **Radii.**

  | Token | Used for |
  |---|---|
  | `radius-xs` | Heat cells, kbd keys, window controls |
  | `radius-sm` | Inputs, service codes, dock items |
  | `radius-md` | Windows, cards, the dock, the palette |
  | `radius-pill` | Buttons, badges, the switch, dots |
- **Lines inside windows.** Ledger rows and facts are separated by 1px dashed `edge` lines. Section tops use a 1.5px solid `edge` line.

## Motion

| Property | Value | Used for |
|---|---|---|
| `--dur-fast` | 150ms | Color and button changes |
| `--dur` | 250ms | Hover lifts and switches |
| `--dur-pop` | 700ms | Windows popping in |
| `--ease-out` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Most movement |
| `--ease-spring` | `cubic-bezier(0.2, 0.9, 0.3, 1.35)` | Pop-ins, the dock, the switch thumb |

These properties live in `components/bundle.css`.

- **On load.** Windows pop in 100ms apart (scale from 0.92 and rise 10px). After that, nothing moves on its own except live dots pinging and a few of the busiest heat cells glowing slowly.
- **Route changes.** Use the View Transitions API, and give each window a `view-transition-name` so it morphs into its page.
- **Reduced motion.** Under `prefers-reduced-motion: reduce`, drop the pop-ins, lifts, springs, pings and glows. Dragging still works.
- No parallax, WebGL, cursor followers or typing effects.

## States

- **Hover.** Windows and buttons lift onto a hard shadow. Rows tint to `well`, and their titles turn `signal`.
- **Focus.** Every interactive element uses `focus-ring`: a 2px gap, then a solid 2px ring. The ring is lime in Pulse and ink in Sage.
- **Selected.** `signal-soft` in the palette. A 2px `signal` underline in the menu bar.
- **Disabled.** 50% opacity, no lift, and the label is kept.
- **Loading.** Say what is happening ("Syncing…") with a pulsing `accent` badge. Never put a spinner over content.

## Iconography

- `Icon` is the Atlas glyph set: a 24px grid, a 1.5px stroke, round caps and joins, drawn in `currentColor`.
- For a glyph that isn't in the set, draw it on the same grid and stroke, or take it from Lucide.
- Services appear as `ServiceCode` stamps (GH, WK, LF, TG…) and dock items, never as brand logos. If a page truly needs a brand mark, use the brand's official SVG unchanged (Simple Icons has them). Never redraw one.
- The only "logo" is the 10px lime square before the name in the menu bar.

## Accessibility

- Dragging windows is a bonus, not a way in. The DOM order of `Desktop` items is the reading order, and every window is a `<section>` named by its title.
- Contrast was checked for both themes. Every text pair named in a token's usage note passes 4.5:1, and controls, focus rings and heat steps pass 3:1. The one exception is `signal` on the Sage desk, which is why it is only used inside windows.

## Using this system

- **Tokens** are CSS custom properties from `tokens.css` (`var(--lime)`, `var(--space-4)`, `var(--font-mono)`), plus a class per type style (`.display-xl`, `.mono-caps`). Add `.at-dotgrid` to any element to give it the desk's dot grid.
- **Components** are React 18 function components on `window.Atlas`, styled by `components/bundle.css` with `at-`-prefixed class names. Their props are typed in `components/index.d.ts`.
- **Owner-only screens** (connections, automations, the sync log) follow the "Connections and automation" section.
