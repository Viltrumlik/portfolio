// Digital rain: <canvas data-island="rain" class="fx-rain" aria-hidden="true">, fixed behind the page.
// ~24 fps, DPR capped at 2, pauses while the tab is hidden. Reduced motion: one faint static frame.

import { fitCanvas, frameLoop, prefersReducedMotion, randomGlyph, themeColours, type Colours, type Loop } from './motion';

const FONT_PX = 14;
const FPS = 24;

export const rainColumns = (width: number, fontPx: number = FONT_PX): number => Math.max(1, Math.ceil(width / fontPx));

/** Moves every drop down a row; a drop past the last row restarts at the top with ~2.5% chance per frame. */
export function stepDrops(drops: number[], rows: number, rand: () => number = Math.random): void {
  for (let i = 0; i < drops.length; i++) {
    if (drops[i] > rows && rand() > 0.975) drops[i] = 0;
    else drops[i]++;
  }
}

export interface Rain {
  readonly running: boolean;
  destroy(): void;
}

export function initRain(canvas: HTMLCanvasElement): Rain | null {
  const doc = canvas.ownerDocument;
  const win = doc.defaultView ?? window;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;

  let colours: Colours = themeColours(doc);
  let width = 0;
  let height = 0;
  let drops: number[] = [];

  const resize = () => {
    width = win.innerWidth;
    height = win.innerHeight;
    fitCanvas(canvas, ctx, width, height);
    const cols = rainColumns(width);
    const rows = Math.ceil(height / FONT_PX);
    drops = Array.from({ length: cols }, (_, i) => drops[i] ?? Math.floor(Math.random() * -rows));
    ctx.font = `${FONT_PX}px "JetBrains Mono", ui-monospace, monospace`;
    ctx.textBaseline = 'top';
    ctx.fillStyle = colours.desk;
    ctx.fillRect(0, 0, width, height);
  };

  const draw = () => {
    ctx.globalAlpha = 0.12;
    ctx.fillStyle = colours.desk;
    ctx.fillRect(0, 0, width, height);
    ctx.globalAlpha = 1;
    for (let i = 0; i < drops.length; i++) {
      if (drops[i] < 0) continue;
      ctx.fillStyle = Math.random() > 0.94 ? colours.hot : colours.phosphor;
      ctx.fillText(randomGlyph(), i * FONT_PX, drops[i] * FONT_PX);
    }
    stepDrops(drops, Math.ceil(height / FONT_PX));
  };

  const drawStatic = () => {
    ctx.fillStyle = colours.desk;
    ctx.fillRect(0, 0, width, height);
    ctx.globalAlpha = 0.35;
    ctx.fillStyle = colours.dim;
    const rows = Math.ceil(height / FONT_PX);
    for (let c = 0; c < drops.length; c++) {
      for (let r = 0; r < rows; r++) if (Math.random() > 0.9) ctx.fillText(randomGlyph(), c * FONT_PX, r * FONT_PX);
    }
    ctx.globalAlpha = 1;
  };

  resize();
  const still = prefersReducedMotion(win);
  let loop: Loop | null = null;
  if (still) drawStatic();
  else {
    loop = frameLoop(draw, FPS, doc);
    loop.start();
  }

  let pending = 0;
  const onResize = () => {
    win.clearTimeout(pending);
    pending = win.setTimeout(() => {
      resize();
      if (still) drawStatic();
    }, 120);
  };
  const onTheme = () => {
    colours = themeColours(doc);
    if (still) drawStatic();
  };
  win.addEventListener('resize', onResize);
  doc.addEventListener('atlas:themechange', onTheme);

  return {
    get running() {
      return loop?.running ?? false;
    },
    destroy() {
      loop?.destroy();
      win.removeEventListener('resize', onResize);
      doc.removeEventListener('atlas:themechange', onTheme);
    },
  };
}
