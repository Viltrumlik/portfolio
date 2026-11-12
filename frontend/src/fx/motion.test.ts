import { afterEach, describe, expect, it, vi } from 'vitest';
import { cssVar, finePointer, frameLoop, GLYPHS, prefersReducedMotion, randomGlyph } from './motion';

function stubMatchMedia(matches: Record<string, boolean>) {
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (q: string) => ({ matches: !!matches[q], media: q, addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList,
  );
}

function setHidden(hidden: boolean) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden });
  document.dispatchEvent(new Event('visibilitychange'));
}

afterEach(() => {
  vi.useRealTimers();
  setHidden(false);
  document.documentElement.removeAttribute('style');
});

describe('media helpers', () => {
  it('treat a missing matchMedia as no preference and a coarse pointer', () => {
    const win = { matchMedia: undefined } as unknown as Window;
    expect(prefersReducedMotion(win)).toBe(false);
    expect(finePointer(win)).toBe(false);
  });

  it('read the media queries', () => {
    stubMatchMedia({ '(prefers-reduced-motion: reduce)': true, '(pointer: fine)': true });
    expect(prefersReducedMotion(window)).toBe(true);
    expect(finePointer(window)).toBe(true);
  });
});

describe('cssVar', () => {
  it('returns the custom property value, trimmed', () => {
    document.documentElement.style.setProperty('--phosphor', ' #00ff41 ');
    expect(cssVar('--phosphor', document.documentElement, '#fff')).toBe('#00ff41');
  });

  it('falls back when the property is unset', () => {
    expect(cssVar('--nope', document.documentElement, '#fff')).toBe('#fff');
  });
});

describe('glyphs', () => {
  it('picks from the glyph set', () => {
    for (let i = 0; i < 50; i++) expect(GLYPHS).toContain(randomGlyph());
  });
});

describe('frameLoop', () => {
  function fakeRaf() {
    vi.useFakeTimers();
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => setTimeout(() => cb(Date.now()), 16) as unknown as number);
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation((id) => clearTimeout(id));
  }

  it('throttles ticks to the requested rate', () => {
    fakeRaf();
    const tick = vi.fn();
    const loop = frameLoop(tick, 20, document); // every 50 ms
    loop.start();
    vi.advanceTimersByTime(1000);
    expect(tick.mock.calls.length).toBeGreaterThanOrEqual(17);
    expect(tick.mock.calls.length).toBeLessThanOrEqual(21);
    loop.stop();
    const n = tick.mock.calls.length;
    vi.advanceTimersByTime(500);
    expect(tick.mock.calls.length).toBe(n);
  });

  it('pauses while the document is hidden and resumes after', () => {
    fakeRaf();
    const tick = vi.fn();
    const loop = frameLoop(tick, 30, document);
    loop.start();
    vi.advanceTimersByTime(200);
    setHidden(true);
    const n = tick.mock.calls.length;
    vi.advanceTimersByTime(1000);
    expect(tick.mock.calls.length).toBe(n);
    expect(loop.running).toBe(false);
    setHidden(false);
    vi.advanceTimersByTime(200);
    expect(tick.mock.calls.length).toBeGreaterThan(n);
    loop.destroy();
  });

  it('does not resume on visibility if it was stopped', () => {
    fakeRaf();
    const tick = vi.fn();
    const loop = frameLoop(tick, 30, document);
    loop.start();
    loop.stop();
    setHidden(true);
    setHidden(false);
    vi.advanceTimersByTime(500);
    expect(tick).not.toHaveBeenCalled();
    loop.destroy();
  });
});

describe('fitCanvas', () => {
  it('caps the pixel ratio at the given maximum', async () => {
    const { fitCanvas } = await import('./motion');
    vi.stubGlobal('devicePixelRatio', 3);
    const canvas = document.createElement('canvas');
    const ctx = { setTransform: vi.fn() } as unknown as CanvasRenderingContext2D;
    fitCanvas(canvas, ctx, 100, 50, 1);
    expect([canvas.width, canvas.height]).toEqual([100, 50]);
    fitCanvas(canvas, ctx, 100, 50);
    expect([canvas.width, canvas.height]).toEqual([200, 100]);
    vi.unstubAllGlobals();
  });
});

