Atlas is the design system for a backend developer's portfolio that runs like a small operating system on a green-screen terminal. The home page is a dense desk of terminal windows over falling digital rain:
- an about window that decodes the owner's handle;
- a terminal that types a real shell session;
- the GitHub graph;
- projects as an `ls -la` listing;
- the stack as a config file;
- the local time.

A menu bar runs across the top and a dock across the bottom. Everything glows in one phosphor colour, and everything on the desk is real data from connected services (GitHub, WakaTime, Last.fm, Telegram). This is version 3, the "Matrix" edition. It replaces v2 (the Pulse and Sage themes with hard offset shadows).

## Principles

- **A desktop, not a document.** The hero is a `Desktop` of `Window`s under a `SiteHeader` menu bar, with a `Dock` at the bottom. Below it, pages scroll normally, but content still lives in windows.
- **Dense, with no holes.** The desk packs nine windows into three columns. A window with nothing to show is left out and the windows below it move up.
- **Data is the ornament.** Every window shows something true and current. The terminal types real commands with real output: the handle, the location, the project count, the last three activity events, availability. If a source isn't connected, its window disappears. Never show fake data or a fake command result.
- **One phosphor.** Each theme has one hue: `phosphor`, also reachable as `lime` and `signal`. Everything else is that hue dimmed (`phosphor-dim`, `ink-muted`), brightened (`phosphor-hot`) or blooming (`glow`). There is no second accent.
- **Glow, not shadow.** Depth comes from phosphor bloom (`shadow-hard`, `shadow-lift`, `text-glow`), never from offset shadows. The only gradients are the CRT scanlines and vignette.
- **Maximal, but every effect can step aside.** Rain, the boot screen, decoding headings, the typing terminal, the cursor trail, page transitions and sound all layer on top of server-rendered HTML. Under reduced motion they stop. Sound stays off until the visitor turns it on.

## Content fundamentals

- Write in the first person singular, plainly and specifically: "I build server-side systems, REST APIs and bots that keep working after launch." Avoid vague self-praise.
- Write titles, buttons and nav in sentence case in the source. CSS uppercases window titles, labels, buttons, badges and the menu bar, so never type capitals for effect.
- CSS also draws the brackets around buttons (`[ SYNC NOW ]`), the `■` before window titles and the `> ` before field labels. Don't type them into the copy.
- Title windows like files, in lowercase:
  - "about.sys", "terminal — tty1", "now.app", "commits.log";
  - "projects/", "links.sh", "stack.cfg", "activity.feed", "sys.info";
  - "connections/github".

  It's the one place the system plays along with its metaphor.
- The terminal transcript uses real-looking commands (`$ whoami`, `$ cat ~/.location`, `$ ls ~/projects | wc -l`, `$ tail -n 3 ~/activity.log`, `$ status`). Each one prints only data the site actually holds.
- Start each button with a verb and name its object: "Sync now", "Download CV", "Reconnect Last.fm".
- No emoji, in copy or as icons. The rain's half-width katakana are decoration only, never content.
- **Numbers and times.**
  - Write numbers as numerals with units: "4h 12m", "14 repos", "99.6%".
  - Use 24-hour times in the owner's zone (UTC+5): "14:02".
  - Under an hour, use relative time: "4 min ago".
- An error says what failed, why, and what to do next: "Last.fm rejected the API key (error 10). Paste a new key to resume syncing."
- UI copy is English. Project names keep their own language ("Pul Olami"). Uzbek text uses ʻ (U+02BB) in oʻ and gʻ.

## Color

There are three phosphor themes, all dark (`color-scheme: dark`):

| Theme | id | Phosphor | Desk |
|---|---|---|---|
| Phosphor green (default) | `green` | `#00ff41` | `#010802` |
| Amber | `amber` | `#ffb000` | `#0a0600` |
| Ice | `ice` | `#5ee7ff` | `#01060a` |

- **Switching.** "Switch theme" in the footer and in ⌘K cycles green → amber → ice.
- **Remembering.** The choice is stored in the `theme` cookie, so the server renders the right theme with no flash.
- **Fallback.** An unknown value falls back to green, and so do v2's `dark` and `light`.

The rest of this section names the color tokens by role.

- **Surfaces.**
  - `desk`: the ground behind the rain.
  - `window`: the window surface. It is 86% opaque so the rain shows faintly through, with a 2px backdrop blur.
  - `window-bar`: inactive title bars.
  - `well`: kbd keys, service codes, dock items, badges and empty heat cells.
  - `desk-dot`: the optional `.at-dotgrid`.
- **Text.**
  - `ink` (a phosphor-tinted near-white) for reading text.
  - `ink-muted` for metadata, inactive title bars and labels.
- **Lines.**
  - `edge`: window outlines and the dashed rules inside windows. It is decorative (about 2:1).
  - `edge-strong`: any border that marks a control, and the outline of a hovered window.
- **Accent.**
  - `phosphor` is the theme's hue. In v3, `lime` and `signal` equal it; they are kept so v2 components work unchanged.
  - Use `lime` as a fill: the active title bar, the primary button, the switch when on, the active dock item. Put `on-lime` text on it and outline it with `lime-edge`.
  - Use `signal` as text or a mark: links, display type, numerals, the terminal, section indexes. Show `signal` text on `signal-soft` for hovered rows and the selected palette row.
- **Light levels.**
  - `phosphor-hot` is the white-hot core: rain heads and the primary button on hover.
  - `phosphor-dim` is decoration only: rain trails and the `//` and `## ` prefixes. It is under 4.5:1, so it never colours text; `frontend/src/atlas/contrast.test.ts` fails the frontend tests if it does.
  - `glow` (16% of the hue) and `glow-strong` (45%) only ever appear inside shadows.
- **State.** `danger` is red in every theme and always comes with the alert glyph and a sentence. `danger-soft` is the tint behind it.
- **Data.** `heat-0` to `heat-4` ramp from `well` up to full phosphor. Use them only in the contribution graph and on the cover.

## Type

- **`display` (VT323).** The CRT face, at its single weight (400), always in `signal` with `text-glow`. It sets:
  - `display-xl` (96/84) and `display-lg` (64/58);
  - `headline` (42/40) and section titles (46/42);
  - `numeral` (44/40): stats and the clock;
  - the menu-bar name (26px).
- **`sans` and `mono` are both JetBrains Mono.** In v3 everything that isn't display type is mono:
  - body 15/24 and `body-lg` 16/24;
  - `body-sm` 13/20 and `title` 16/22 bold;
  - `mono` 12/18 for code and timestamps;
  - `label`, `mono-sm` and `mono-caps` at 10–12px bold, uppercased by CSS and tracked 0.12–0.14em.

  Numbers use tabular figures.
- **One `display-xl` per page.** On the home page it is the owner's handle in about.sys, uppercased and decoded on load. Keep running text within `measure` (64ch).
- **Loading.** Both families load from Google Fonts (JetBrains Mono 400/500/700/800, VT323): through the `@import` at the top of `components/bundle.css` here, and through `templates/base.html` on the site.

## Layout

- **Desk hero.**
  - The `SiteHeader` menu bar is sticky at the top. The `Desktop` below it is transparent, so the rain shows through.
  - Windows sit in three columns. Each window has a fixed height and they stack top to bottom with 20px gaps:

    | Column (x, width) | Windows, top to bottom |
    |---|---|
    | 2%, 37% | about.sys 350, commits.log 200, stack.cfg 230 |
    | 40.5%, 33% | terminal — tty1 250, projects/ 220, activity.feed 190 |
    | 75%, 23% | now.app 250, links.sh 170, sys.info 220 |

  - The server works out the positions (`web/desk.py`). It drops windows that have nothing to show and passes `--x`, `--y`, `--w`, `--h` and `--delay` to each window.
  - The desk is as tall as its longest column plus room for the `Dock`, which is centered at the bottom.
  - A window body scrolls if its content runs long.
- **Below the desktop.** Sections scroll as usual inside `container-max` (1240px). Each section is a window opened by a `SectionHeader`. Project lists are `ProjectRow`s in a window; repos are a grid of `RepoCard`s. Reading windows (articles, the about page) are 95% opaque so text never fights the rain.
- **Under 1024px.** The desk becomes one column of windows in reading order, each window as tall as its content. Dragging is off and the dock sticks to the bottom.
- **Under 720px.**
  - The menu bar keeps only the name, the clock and ⌘K.
  - The `ls` permission column hides wherever its window is narrower than 320px.
  - Page gutters are `space-5`.
- **Spacing.** The base unit is 4px, from `space-1` to `space-10`. Window bodies use `space-4` and top-level sections are `space-9` apart.

## Windows, borders, radii and shadows

- **Anatomy.**
  - The title bar is 26px tall and reads `■ TITLE ……… [_][□][x]`. The `■` is in `signal`. The title is bold, uppercase and 10px. CSS draws the three controls from the window's three control elements.
  - The body is padded by `space-4`.
  - The window has a 1px `edge` outline, `radius-md` (6px) corners and the `shadow-hard` bloom (an outer glow plus an inner glow).
- **Active.** The title bar fills with `lime`, takes `on-lime` text and blooms. Only one window on screen is active: the about window on load, then whichever window was touched last.
- **Hover and drag.**
  - On hover the window takes `shadow-lift`, its outline turns `edge-strong`, and its title bar jitters once: a 240ms, two-step glitch with a hue shift.
  - While dragged, the outline turns `signal`. Windows don't tilt or lift in v3.
- **Radii.** Corners are nearly square.

  | Token | Value | Used for |
  |---|---|---|
  | `radius-xs` | 2px | Buttons, inputs, badges, kbd keys, service codes, dock items, the switch |
  | `radius-sm` | 3px | Notes and small panels |
  | `radius-md` | 6px | Windows, cards, the dock, the palette |
  | `radius-pill` | 999px | Kept for studio counters only |
- **Lines inside windows.** Ledger rows, facts, stats, feed rows and section tops use 1px dashed `edge` lines.
- **The CRT glass.** `body::after` lays scanlines (1px dark lines every 3px) and a vignette over the whole page. It sits at z-index 2500 and never takes input.

## Motion

| Property | Value | Used for |
|---|---|---|
| `--dur-fast` | 120ms | Color and button changes |
| `--dur` | 220ms | Hover blooms and switches |
| `--dur-pop` | 650ms | Windows switching on |
| `--ease-out` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Most movement |
| `--ease-spring` | `cubic-bezier(0.2, 0.9, 0.3, 1.35)` | The dock, the switch thumb, row arrows |

These properties live in `components/bundle.css`.

- **On load.** Each window switches on like a CRT: it starts as a thin, overbright line, opens to full height and settles (`at-pop`).
  - The delays are staggered 70ms apart, left to right and then row by row.
  - After that, the only things that keep moving are blinking cursors and live dots, the rain, and a few of the busiest heat cells fading in and out.
- **Blinks, not pings.** Live dots, the menu-bar cursor and the typer cursor blink in hard steps (`steps(1)`), like a terminal.

### Effects

The effects live in `frontend/src/fx`. They are public pages only; the studio keeps the look but has no rain, boot screen, trail or sound. The boot screen loads with the page; everything else loads in a small separate chunk on first use.

| Effect | Markup | What it does | Under reduced motion |
|---|---|---|---|
| Digital rain | `<canvas data-island="rain" class="fx-rain">` | Columns of katakana and digits at 14px, about 24fps, 55% opacity, in the theme's colours, fixed behind the page. Pauses in hidden tabs. | One faint, static frame |
| Boot screen | `<div data-island="bootscreen" class="fx-boot" hidden>` | Once per browser session (`sessionStorage` `atlas:booted`): about a second of BIOS-style log, then a 300ms CRT collapse. Any key, click, wheel or touch skips it. | Never runs |
| Decode | `data-island="decode"` on a heading | Scrambles random glyphs into the heading's own text when it scrolls into view. `data-decode="load"` runs it at load, and `data-decode-repeat="9000"` repeats it. The real text stays in `aria-label` meanwhile. | Plain text |
| Typer | `<pre data-island="typer" data-loop data-max-lines>` | Replays a transcript the server already rendered: `$ ` lines type at 45ms a character, output appears at once, a block cursor blinks. Screen readers get the full transcript. | Static transcript |
| Cursor trail | Document-level | Glyphs drip from the pointer and fade, up to 120 at a time. Fine pointers only. An idle page costs nothing. | Off |
| Sound | `[data-sound-toggle]` in the menu bar | Off by default. WebAudio-synthesised clicks, keystroke ticks and a theme blip, with no audio files. The choice is kept in `localStorage` `atlas:sound`. | Still opt-in |
| Page transitions | `@view-transition { navigation: auto }` | The old page glitches out (180ms), the new one scans in from the top (300ms). | Off |

## States

- **Hover.**
  - Windows bloom and their bars jitter once.
  - Buttons fill with `signal` and glow.
  - Rows tint to `signal-soft` and their titles glow. A project row also gains a `> ` before its index.
- **Focus.** Every interactive element uses `focus-ring`: a 2px `desk` gap, then a solid 2px `phosphor` ring. Inputs light their border and bloom instead.
- **Selected.** `signal-soft` with a 2px `signal` rule on the left in the palette. In the menu bar, the active link is in `signal` with `>` in place of `/`.
- **Disabled.** 45–50% opacity, no glow, and the label is kept.
- **Loading.** Say what is happening ("Syncing…") with a blinking `accent` badge dot. Never put a spinner over content.

## Iconography

- `Icon` is the Atlas glyph set: a 24px grid, a 1.5px stroke, round caps and joins, drawn in `currentColor`.
- For a glyph that isn't in the set, draw it on the same grid and stroke, or take it from Lucide.
- Services appear as `ServiceCode` stamps (GH, WK, LF, TG…) and dock items, never as brand logos. If a page truly needs a brand mark, use the brand's official SVG unchanged (Simple Icons has them). Never redraw one.
- The only "logo" is the blinking block cursor after the name in the menu bar.

## Accessibility

- Dragging windows is a bonus, not a way in. The DOM order of `Desktop` items is the reading order, and every window is a `<section>` named by its title.
- The rain, the trail canvas and the CRT glass are `aria-hidden` and never take the pointer.
- **Measured contrast.** These ratios were measured in all three themes, with the window composited over the desk:
  - `ink` passes 11.7:1 or more on every surface.
  - `ink-muted` passes 5.7:1 or more and `signal` 8:1 or more, also on every surface.
  - `danger` passes 4.9:1 or more on window and well.
  - `on-lime` on `lime` is 10.3:1 or more.
  - Control borders (`edge-strong`) pass 5.3:1 or more, and the focus ring 10.9:1 or more.
- **Dim on purpose.**
  - `phosphor-dim` is only 3.4–4.1:1 on a window, so it is kept to `::before`/`::after` prefixes. Project indexes, stack lines, `ls` permissions and palette group labels use `ink-muted`.
  - `heat-1` is a faint step (about 1.8:1 on a window). The graph's total and legend carry the numbers.

## Using this system

- **Tokens** are CSS custom properties from `tokens.css` (`var(--phosphor)`, `var(--space-4)`, `var(--font-display)`), plus a class per type style (`.display-xl`, `.mono-caps`). Theme them with `data-theme="green|amber|ice"` on `<html>`. Add `.at-dotgrid` to any element for the desk's dot grid, or `.at-glow` for phosphor text.
- **Components** are React 18 function components on `window.Atlas`, styled by `components/bundle.css` with `at-`-prefixed class names. Their props are typed in `components/index.d.ts`. The class names are unchanged from v2, so markup written for v2 picks up the Matrix look as is.
- **Owner-only screens** (connections, automations, the sync log) follow the "Connections and automation" section.
