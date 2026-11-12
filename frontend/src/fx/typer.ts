// Typer island: <pre data-island="typer" [data-loop="4000"] [data-max-lines="9"]>$ cmd\noutput…</pre>.
// The server renders the whole transcript; this replays it as if typed. Lines starting "$ " are typed
// character by character, other lines appear at once.

import { prefersReducedMotion } from './motion';

const CHAR_MS = 45;
const OUTPUT_MS = 90;
const AFTER_COMMAND_MS = 260;

export interface Typer {
  stop(): void;
}

export function initTyper(el: HTMLElement): Typer | null {
  const doc = el.ownerDocument;
  const win = doc.defaultView ?? window;
  const transcript = (el.textContent ?? '').replace(/\s+$/, '');
  if (!transcript || prefersReducedMotion(win)) return null;

  const lines = transcript.split('\n');
  const maxLines = Math.max(1, Number(el.dataset.maxLines) || 9);
  const loopMs = Number(el.dataset.loop) || 0;

  const sr = doc.createElement('span');
  sr.className = 'fx-sr';
  sr.textContent = transcript;
  const screen = doc.createElement('span');
  screen.className = 'fx-typer-screen';
  screen.setAttribute('aria-hidden', 'true');
  const text = doc.createTextNode('');
  const cursor = doc.createElement('span');
  cursor.className = 'fx-cursor';
  screen.append(text, cursor);
  el.textContent = '';
  el.append(sr, screen);

  let shown: string[] = [];
  let line = 0;
  let char = 0;
  let timer = 0;
  let stopped = false;

  const render = (partial: string | null) => {
    const visible = partial === null ? shown : [...shown, partial];
    text.data = visible.slice(-maxLines).join('\n');
  };
  const later = (fn: () => void, ms: number) => {
    if (!stopped) timer = win.setTimeout(fn, ms);
  };

  const step = () => {
    if (line >= lines.length) {
      if (loopMs) later(restart, loopMs);
      return;
    }
    const current = lines[line];
    if (current.startsWith('$ ')) {
      char++;
      if (char < current.length) {
        render(current.slice(0, char));
        return later(step, CHAR_MS);
      }
      shown.push(current);
      render(null);
      line++;
      char = 0;
      return later(step, AFTER_COMMAND_MS);
    }
    shown.push(current);
    render(null);
    line++;
    later(step, OUTPUT_MS);
  };

  const restart = () => {
    shown = [];
    line = 0;
    char = 0;
    render(null);
    later(step, CHAR_MS);
  };

  render(null);
  later(step, CHAR_MS);

  return {
    stop() {
      stopped = true;
      win.clearTimeout(timer);
    },
  };
}
