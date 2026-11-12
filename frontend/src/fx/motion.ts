// Shared helpers for the Matrix effects: media queries, theme colours, glyphs and a throttled frame loop.

/** Half-width katakana, digits and a few symbols — the digital-rain alphabet. */
export const GLYPHS = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789Z:.=*+-<>¦|';

export function randomGlyph(rand: () => number = Math.random): string {
  return GLYPHS[Math.floor(rand() * GLYPHS.length) % GLYPHS.length];
}

function media(win: Window, query: string): boolean {
  try {
    return !!win.matchMedia?.(query)?.matches;
  } catch {
    return false;
  }
}

export const prefersReducedMotion = (win: Window = window): boolean => media(win, '(prefers-reduced-motion: reduce)');
export const finePointer = (win: Window = window): boolean => media(win, '(pointer: fine)');

/** A custom property's computed value (trimmed), or the fallback when unset. */
export function cssVar(name: string, el: Element = document.documentElement, fallback = ''): string {
  const win = el.ownerDocument.defaultView;
  const value = win?.getComputedStyle(el).getPropertyValue(name).trim();
  return value || fallback;
}

export interface Colours {
  phosphor: string;
  hot: string;
  dim: string;
  desk: string;
}

export function themeColours(doc: Document = document): Colours {
  const root = doc.documentElement;
  return {
    phosphor: cssVar('--phosphor', root, '#00ff41'),
    hot: cssVar('--phosphor-hot', root, '#d8ffe0'),
    dim: cssVar('--phosphor-dim', root, '#0a5c1f'),
    desk: cssVar('--desk', root, '#010802'),
  };
}

export interface Loop {
  start(): void;
  stop(): void;
  destroy(): void;
  readonly running: boolean;
}

/**
 * Calls `tick` at most `fps` times a second on animation frames. Pauses while the document is
 * hidden and resumes when it is shown again (only if it was started).
 */
export function frameLoop(tick: (now: number) => void, fps: number, doc: Document = document): Loop {
  const win = doc.defaultView ?? window;
  const raf = win.requestAnimationFrame
    ? win.requestAnimationFrame.bind(win)
    : (cb: FrameRequestCallback) => win.setTimeout(() => cb(Date.now()), 16);
  const caf = win.cancelAnimationFrame ? win.cancelAnimationFrame.bind(win) : (id: number) => win.clearTimeout(id);
  const interval = 1000 / fps;
  let wanted = false;
  let id = 0;
  let last = -Infinity;

  const frame = (now: number) => {
    id = 0;
    if (!wanted || doc.hidden) return;
    const elapsed = now - last;
    if (elapsed >= interval) {
      // Keep the remainder so 16.7 ms frames average out to the target rate instead of rounding down.
      last = Number.isFinite(elapsed) ? now - (elapsed % interval) : now;
      tick(now);
    }
    if (wanted) id = raf(frame);
  };
  const schedule = () => {
    if (!id && wanted && !doc.hidden) id = raf(frame);
  };
  const cancel = () => {
    if (id) caf(id);
    id = 0;
  };
  const onVisibility = () => (doc.hidden ? cancel() : schedule());
  doc.addEventListener('visibilitychange', onVisibility);

  return {
    start() {
      wanted = true;
      schedule();
    },
    stop() {
      wanted = false;
      cancel();
    },
    destroy() {
      wanted = false;
      cancel();
      doc.removeEventListener('visibilitychange', onVisibility);
    },
    get running() {
      return id !== 0;
    },
  };
}

/** Canvas backing size: CSS pixels times devicePixelRatio, capped at 2. */
export function fitCanvas(
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  maxDpr = 2,
): void {
  const win = canvas.ownerDocument.defaultView ?? window;
  const dpr = Math.min(maxDpr, Math.max(1, win.devicePixelRatio || 1));
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
