import { afterEach, describe, expect, it, vi } from 'vitest';
import { FX_ISLANDS, initSiteFx } from './index';
import { LAZY_FX_ISLANDS, initSiteFxLazy, loadFx } from './lazy';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
  document.body.className = '';
});

describe('fx index', () => {
  it('exposes the four islands', () => {
    expect(Object.keys(FX_ISLANDS).sort()).toEqual(['bootscreen', 'decode', 'rain', 'typer']);
    expect(Object.keys(LAZY_FX_ISLANDS).sort()).toEqual(['bootscreen', 'decode', 'rain', 'typer']);
  });

  it('rain ignores elements that are not canvases', () => {
    document.body.innerHTML = '<div data-island="rain"></div>';
    expect(FX_ISLANDS.rain(document.querySelector('div')!)).toBeNull();
  });

  it('initSiteFx is a no-op outside the public site and wires sound once inside it', () => {
    document.body.innerHTML = '<button data-sound-toggle aria-pressed="false"></button>';
    const btn = document.querySelector('button')!;
    initSiteFx(document);
    btn.click();
    expect(btn.getAttribute('aria-pressed')).toBe('false');

    document.body.classList.add('at-site');
    initSiteFx(document);
    initSiteFx(document);
    btn.click();
    expect(btn.getAttribute('aria-pressed')).toBe('true'); // one listener, not two (two would flip back)
  });
});

describe('fx lazy', () => {
  it('loads the chunk and runs the real island', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('IntersectionObserver', undefined);
    document.body.innerHTML = '<h1 data-island="decode" data-decode="load">ABC</h1>';
    const h = document.querySelector('h1')!;
    await LAZY_FX_ISLANDS.decode(h);
    vi.advanceTimersByTime(30);
    expect(h.getAttribute('aria-label')).toBe('ABC');
    vi.advanceTimersByTime(3000);
    expect(h.textContent).toBe('ABC');
  });

  it('initSiteFxLazy skips non-site pages', async () => {
    const spy = vi.fn();
    initSiteFxLazy(document, spy);
    await loadFx();
    expect(spy).not.toHaveBeenCalled();
  });
});
