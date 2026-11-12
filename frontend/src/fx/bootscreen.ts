// Boot screen: <div data-island="bootscreen" class="fx-boot" data-name="VILTRUMLIK" hidden></div>.
// Once per browser session, a ~1 s BIOS-style log over the (already rendered) page, then a CRT
// collapse. Any key, click, wheel or touch skips it. Never runs with reduced motion.

import { prefersReducedMotion } from './motion';

export const BOOT_KEY = 'atlas:booted';
const LINE_MS = 120;
const HOLD_MS = 260;
const EXIT_MS = 300;
const SKIP_EVENTS = ['keydown', 'pointerdown', 'wheel', 'touchstart'] as const;

function alreadyBooted(win: Window): boolean {
  try {
    if (win.sessionStorage.getItem(BOOT_KEY)) return true;
    win.sessionStorage.setItem(BOOT_KEY, '1');
    return false;
  } catch {
    return true; // no storage: never risk showing it on every page
  }
}

export function bootLines(name: string): string[] {
  return [
    'ATLAS BIOS v3.0 · phosphor display .... ok',
    'memory check ........................ 640K ok',
    'mounting /projects .................. ok',
    'loading phosphor drivers .......... ok',
    `decrypting identity ................. ${name}`,
    '> welcome, visitor_',
  ];
}

export function initBootscreen(el: HTMLElement): void {
  const doc = el.ownerDocument;
  const win = doc.defaultView ?? window;
  const root = doc.documentElement;
  if (prefersReducedMotion(win) || alreadyBooted(win)) {
    el.remove();
    return;
  }

  const log = doc.createElement('pre');
  log.className = 'fx-boot__log';
  el.replaceChildren(log);
  el.setAttribute('aria-hidden', 'true');
  el.hidden = false;
  root.dataset.booting = '';

  const lines = bootLines((el.dataset.name || 'ATLAS').toUpperCase());
  const timers: number[] = [];
  let leaving = false;

  const cleanup = () => {
    timers.forEach((t) => win.clearTimeout(t));
    SKIP_EVENTS.forEach((type) => doc.removeEventListener(type, skip, true));
  };
  const leave = () => {
    if (leaving) return;
    leaving = true;
    cleanup();
    el.classList.add('fx-boot--out');
    win.setTimeout(() => {
      el.remove();
      delete root.dataset.booting;
    }, EXIT_MS);
  };
  function skip() {
    leave();
  }

  lines.forEach((line, i) => {
    timers.push(win.setTimeout(() => (log.textContent += (i ? '\n' : '') + line), i * LINE_MS));
  });
  timers.push(win.setTimeout(leave, lines.length * LINE_MS + HOLD_MS));
  SKIP_EVENTS.forEach((type) => doc.addEventListener(type, skip, { capture: true, passive: true }));
}
