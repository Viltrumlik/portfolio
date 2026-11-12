import { afterEach, describe, expect, it, vi } from 'vitest';
import { initDecode, scrambleFrame } from './decode';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
});

function el(html: string): HTMLElement {
  document.body.innerHTML = html;
  return document.querySelector('[data-island="decode"]')!;
}

describe('scrambleFrame', () => {
  it('keeps length, spaces and the revealed prefix', () => {
    const out = scrambleFrame('HELLO WORLD', 0.5);
    expect(out).toHaveLength(11);
    expect(out[5]).toBe(' ');
    expect(out.slice(0, 5)).toBe('HELLO');
  });

  it('is the target at progress 1 and fully scrambled at 0', () => {
    expect(scrambleFrame('VILTRUMLIK', 1)).toBe('VILTRUMLIK');
    const zero = scrambleFrame('AAAAAAAAAAAAAAAAAAAA', 0, () => 0.999);
    expect(zero).not.toBe('AAAAAAAAAAAAAAAAAAAA');
  });
});

describe('initDecode', () => {
  it('without IntersectionObserver runs immediately and ends on the original text', () => {
    vi.useFakeTimers();
    vi.stubGlobal('IntersectionObserver', undefined);
    const h = el('<h1 data-island="decode">VILTRUMLIK</h1>');
    initDecode(h);
    vi.advanceTimersByTime(60);
    expect(h.getAttribute('aria-label')).toBe('VILTRUMLIK');
    expect(h.textContent).toHaveLength(10);
    vi.advanceTimersByTime(3000);
    expect(h.textContent).toBe('VILTRUMLIK');
    expect(h.hasAttribute('aria-label')).toBe(false);
  });

  it('keeps an existing aria-label', () => {
    vi.useFakeTimers();
    vi.stubGlobal('IntersectionObserver', undefined);
    const h = el('<h1 data-island="decode" aria-label="Name">ABC</h1>');
    initDecode(h);
    vi.advanceTimersByTime(3000);
    expect(h.getAttribute('aria-label')).toBe('Name');
  });

  it('waits for the element to enter the viewport', () => {
    vi.useFakeTimers();
    let fire: (entries: Partial<IntersectionObserverEntry>[]) => void = () => {};
    const unobserve = vi.fn();
    vi.stubGlobal(
      'IntersectionObserver',
      class {
        constructor(cb: (e: Partial<IntersectionObserverEntry>[]) => void) {
          fire = cb;
        }
        observe() {}
        unobserve = unobserve;
        disconnect() {}
      },
    );
    const h = el('<h2 data-island="decode">Selected work</h2>');
    initDecode(h);
    vi.advanceTimersByTime(500);
    expect(h.hasAttribute('aria-label')).toBe(false);
    fire([{ isIntersecting: true, target: h }]);
    vi.advanceTimersByTime(30);
    expect(h.getAttribute('aria-label')).toBe('Selected work');
    expect(unobserve).toHaveBeenCalledWith(h);
    vi.advanceTimersByTime(3000);
    expect(h.textContent).toBe('Selected work');
  });

  it('data-decode="load" runs at once even with IntersectionObserver', () => {
    vi.useFakeTimers();
    const observe = vi.fn();
    vi.stubGlobal('IntersectionObserver', class { observe = observe; unobserve() {} disconnect() {} });
    const h = el('<h1 data-island="decode" data-decode="load">NAME</h1>');
    initDecode(h);
    vi.advanceTimersByTime(30);
    expect(h.getAttribute('aria-label')).toBe('NAME');
    expect(observe).not.toHaveBeenCalled();
  });

  it('repeats on an interval', () => {
    vi.useFakeTimers();
    vi.stubGlobal('IntersectionObserver', undefined);
    const h = el('<h1 data-island="decode" data-decode="load" data-decode-repeat="5000">NAME</h1>');
    initDecode(h);
    vi.advanceTimersByTime(3000);
    expect(h.hasAttribute('aria-label')).toBe(false);
    vi.advanceTimersByTime(2050);
    expect(h.getAttribute('aria-label')).toBe('NAME');
    vi.advanceTimersByTime(3000);
    expect(h.textContent).toBe('NAME');
  });

  it('does nothing with reduced motion', () => {
    vi.useFakeTimers();
    vi.stubGlobal('IntersectionObserver', undefined);
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (q: string) => ({ matches: q.includes('reduce'), media: q }) as unknown as MediaQueryList,
    );
    const h = el('<h1 data-island="decode">NAME</h1>');
    initDecode(h);
    vi.advanceTimersByTime(50);
    expect(h.textContent).toBe('NAME');
    expect(h.hasAttribute('aria-label')).toBe(false);
  });
});
