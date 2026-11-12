// Cursor trail: glyphs that drip from the pointer and fade. Fine pointers only, never with reduced
// motion. The loop runs only while particles are alive, so an idle page costs nothing.

import { finePointer, fitCanvas, frameLoop, prefersReducedMotion, randomGlyph, themeColours } from './motion';

export const TRAIL_CAP = 120;
const LIFE = 1;
const FPS = 30;

interface Particle {
  x: number;
  y: number;
  vy: number;
  life: number;
  glyph: string;
}

export interface Trail {
  count(): number;
  destroy(): void;
}

export function initCursorTrail(doc: Document = document): Trail | null {
  const win = doc.defaultView ?? window;
  if (!finePointer(win) || prefersReducedMotion(win)) return null;

  const canvas = doc.createElement('canvas');
  canvas.className = 'fx-trail';
  canvas.setAttribute('aria-hidden', 'true');
  doc.body.append(canvas);
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    canvas.remove();
    return null;
  }

  let colour = themeColours(doc).phosphor;
  let width = 0;
  let height = 0;
  const particles: Particle[] = [];

  const resize = () => {
    width = win.innerWidth;
    height = win.innerHeight;
    fitCanvas(canvas, ctx, width, height, 1);
    ctx.font = '13px "JetBrains Mono", ui-monospace, monospace';
  };

  const tick = () => {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = colour;
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.life -= 0.035;
      p.y += p.vy;
      p.vy += 0.12;
      if (p.life <= 0) {
        particles.splice(i, 1);
        continue;
      }
      if (Math.random() > 0.85) p.glyph = randomGlyph();
      ctx.globalAlpha = p.life;
      ctx.fillText(p.glyph, p.x, p.y);
    }
    ctx.globalAlpha = 1;
    if (!particles.length) loop.stop();
  };
  const loop = frameLoop(tick, FPS, doc);

  const spawn = (x: number, y: number) => {
    const n = Math.random() > 0.7 ? 2 : 1;
    for (let i = 0; i < n; i++) {
      if (particles.length >= TRAIL_CAP) particles.shift();
      particles.push({ x: x + (Math.random() - 0.5) * 10, y, vy: 0.4 + Math.random() * 0.8, life: LIFE, glyph: randomGlyph() });
    }
    loop.start();
  };

  const onMove = (e: Event) => {
    const { clientX, clientY } = e as PointerEvent;
    spawn(clientX, clientY);
  };
  const onTheme = () => (colour = themeColours(doc).phosphor);

  resize();
  doc.addEventListener('pointermove', onMove, { passive: true });
  win.addEventListener('resize', resize);
  doc.addEventListener('atlas:themechange', onTheme);

  return {
    count: () => particles.length,
    destroy() {
      loop.destroy();
      doc.removeEventListener('pointermove', onMove);
      win.removeEventListener('resize', resize);
      doc.removeEventListener('atlas:themechange', onTheme);
      canvas.remove();
    },
  };
}
