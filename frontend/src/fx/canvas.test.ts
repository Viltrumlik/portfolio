import { afterEach, describe, expect, it, vi } from 'vitest';
import { initRain, rainColumns, stepDrops, struggling } from './rain';
import { initCursorTrail, TRAIL_CAP } from './trail';

function fakeCtx() {
  return {
    setTransform: vi.fn(),
    fillRect: vi.fn(),
    fillText: vi.fn(),
    clearRect: vi.fn(),
    globalAlpha: 1,
    fillStyle: '',
    font: '',
    textBaseline: '',
  } as unknown as CanvasRenderingContext2D;
}

function stubMatchMedia(matches: Record<string, boolean>) {
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (q: string) => ({ matches: !!matches[q], media: q }) as unknown as MediaQueryList,
  );
}

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('rain helpers', () => {
  it('calls a device struggling only on a sustained slow median, not one long pause', () => {
    const healthy = Array(30).fill(50);
    expect(struggling(healthy, 50)).toBe(false);
    expect(struggling([...healthy.slice(1), 10_000], 50)).toBe(false); // a hidden tab coming back
    expect(struggling(Array(30).fill(150), 50)).toBe(true);
    expect(struggling(Array(10).fill(150), 50)).toBe(false); // not enough evidence yet
  });

  it('derives the column count from width and glyph size', () => {
    expect(rainColumns(1400, 14)).toBe(100);
    expect(rainColumns(10, 14)).toBe(1);
  });

  it('advances drops and resets those past the bottom (by chance)', () => {
    const drops = [5, 50, 50];
    stepDrops(drops, 40, () => 0.99);
    expect(drops).toEqual([6, 0, 0]);
    const keep = [50];
    stepDrops(keep, 40, () => 0.1);
    expect(keep).toEqual([51]);
  });
});

describe('initRain', () => {
  it('returns null without a 2d context', () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
    document.body.innerHTML = '<canvas data-island="rain"></canvas>';
    expect(initRain(document.querySelector('canvas')!)).toBeNull();
  });

  it('draws at 1x even on dense screens: the rain is faint, and pixels are what make it slow', () => {
    vi.useFakeTimers();
    const ctx = fakeCtx();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(ctx as never);
    vi.stubGlobal('devicePixelRatio', 3);
    document.body.innerHTML = '<canvas data-island="rain"></canvas>';
    const canvas = document.querySelector('canvas')!;
    const rain = initRain(canvas)!;
    expect(canvas.width).toBe(window.innerWidth);
    expect(canvas.height).toBe(window.innerHeight);
    rain.destroy();
    vi.unstubAllGlobals();
  });

  function pumpFrames(gapMs: number, frames: number) {
    const queue: FrameRequestCallback[] = [];
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => queue.push(cb));
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {});
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(fakeCtx() as never);
    document.body.innerHTML = '<canvas data-island="rain"></canvas>';
    const rain = initRain(document.querySelector('canvas')!)!;
    let t = 1000;
    for (let i = 0; i < frames && queue.length; i++) {
      t += gapMs;
      queue.shift()!(t);
    }
    return rain;
  }

  it('settles into a still frame when the device cannot keep up', () => {
    const rain = pumpFrames(250, 80); // 4 frames a second
    expect(rain.running).toBe(false);
  });

  it('keeps raining at a healthy frame rate', () => {
    const rain = pumpFrames(1000 / 60, 600);
    expect(rain.running).toBe(true);
    rain.destroy();
  });

  it('draws one static frame and does not animate under reduced motion', () => {
    vi.useFakeTimers();
    stubMatchMedia({ '(prefers-reduced-motion: reduce)': true });
    const ctx = fakeCtx();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(ctx as never);
    const raf = vi.spyOn(window, 'requestAnimationFrame');
    document.body.innerHTML = '<canvas data-island="rain"></canvas>';
    const rain = initRain(document.querySelector('canvas')!)!;
    expect((ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(0);
    expect(rain.running).toBe(false);
    expect(raf).not.toHaveBeenCalled();
  });
});

describe('initCursorTrail', () => {
  it('is off without a fine pointer', () => {
    stubMatchMedia({});
    expect(initCursorTrail(document)).toBeNull();
    expect(document.querySelector('.fx-trail')).toBeNull();
  });

  it('is off with reduced motion', () => {
    stubMatchMedia({ '(pointer: fine)': true, '(prefers-reduced-motion: reduce)': true });
    expect(initCursorTrail(document)).toBeNull();
  });

  it('spawns glyph particles on pointermove, capped', () => {
    vi.useFakeTimers();
    stubMatchMedia({ '(pointer: fine)': true });
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(fakeCtx() as never);
    const trail = initCursorTrail(document)!;
    const canvas = document.querySelector('.fx-trail')!;
    expect(canvas.getAttribute('aria-hidden')).toBe('true');
    document.dispatchEvent(new MouseEvent('pointermove', { clientX: 10, clientY: 10 }));
    expect(trail.count()).toBeGreaterThan(0);
    for (let i = 0; i < 500; i++) document.dispatchEvent(new MouseEvent('pointermove', { clientX: i, clientY: i }));
    expect(trail.count()).toBeLessThanOrEqual(TRAIL_CAP);
    trail.destroy();
    expect(document.querySelector('.fx-trail')).toBeNull();
  });

  it('removes its canvas when there is no 2d context', () => {
    stubMatchMedia({ '(pointer: fine)': true });
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
    expect(initCursorTrail(document)).toBeNull();
    expect(document.querySelector('.fx-trail')).toBeNull();
  });
});
