// Decode island: <h1 data-island="decode" [data-decode="load"] [data-decode-repeat="8000"]>Text</h1>.
// Scrambles from random glyphs into the element's own text when it scrolls into view (or on load).

import { prefersReducedMotion, randomGlyph } from './motion';

const FRAME_MS = 30;

/** The text with the first `progress` share revealed and the rest as random glyphs (spaces kept). */
export function scrambleFrame(target: string, progress: number, rand: () => number = Math.random): string {
  const revealed = Math.floor(Math.max(0, Math.min(1, progress)) * target.length);
  let out = '';
  for (let i = 0; i < target.length; i++) {
    const ch = target[i];
    out += i < revealed || /\s/.test(ch) ? ch : randomGlyph(rand);
  }
  return out;
}

export interface Decoder {
  run(): void;
  stop(): void;
}

export function initDecode(el: HTMLElement): Decoder | null {
  const doc = el.ownerDocument;
  const win = doc.defaultView ?? window;
  const text = el.textContent ?? '';
  if (!text.trim() || prefersReducedMotion(win)) return null;

  const hadLabel = el.hasAttribute('aria-label');
  const frames = Math.min(40, Math.max(14, Math.round(text.length * 2.2)));
  let timer = 0;
  let repeat = 0;
  let observer: IntersectionObserver | null = null;

  const finish = () => {
    win.clearTimeout(timer);
    timer = 0;
    el.textContent = text;
    el.classList.remove('fx-decoding');
    if (!hadLabel) el.removeAttribute('aria-label');
  };

  const run = () => {
    if (timer) return;
    if (!hadLabel) el.setAttribute('aria-label', text);
    el.classList.add('fx-decoding');
    let frame = 0;
    const step = () => {
      frame++;
      if (frame >= frames) return finish();
      el.textContent = scrambleFrame(text, frame / frames);
      timer = win.setTimeout(step, FRAME_MS);
    };
    timer = win.setTimeout(step, 0);
  };

  const startRepeat = () => {
    const every = Number(el.dataset.decodeRepeat);
    if (every > 0 && !repeat) repeat = win.setInterval(() => !doc.hidden && run(), every);
  };

  const IO = (win as Window & { IntersectionObserver?: typeof IntersectionObserver }).IntersectionObserver;
  if (el.dataset.decode === 'load' || typeof IO !== 'function') {
    run();
    startRepeat();
  } else {
    observer = new IO((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer?.unobserve(entry.target);
        run();
        startRepeat();
      }
    });
    observer.observe(el);
  }

  return {
    run,
    stop() {
      observer?.disconnect();
      win.clearInterval(repeat);
      repeat = 0;
      if (timer) finish();
    },
  };
}
