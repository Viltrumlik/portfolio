import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BOOT_KEY, initBootscreen } from './bootscreen';

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
  delete document.documentElement.dataset.booting;
});

function mount() {
  document.body.innerHTML = '<div data-island="bootscreen" class="fx-boot" data-name="VILTRUMLIK" hidden></div>';
  return document.querySelector<HTMLElement>('.fx-boot')!;
}

describe('initBootscreen', () => {
  it('plays once: shows the log, locks scroll, then removes itself', () => {
    vi.useFakeTimers();
    const el = mount();
    initBootscreen(el);
    expect(el.hidden).toBe(false);
    expect(el.getAttribute('aria-hidden')).toBe('true');
    expect(document.documentElement.dataset.booting).toBe('');
    expect(sessionStorage.getItem(BOOT_KEY)).toBe('1');
    vi.advanceTimersByTime(700);
    expect(el.textContent).toContain('VILTRUMLIK');
    vi.advanceTimersByTime(2000);
    expect(el.isConnected).toBe(false);
    expect(document.documentElement.dataset.booting).toBeUndefined();
  });

  it('is skipped on later visits in the same session', () => {
    sessionStorage.setItem(BOOT_KEY, '1');
    const el = mount();
    initBootscreen(el);
    expect(el.isConnected).toBe(false);
    expect(document.documentElement.dataset.booting).toBeUndefined();
  });

  it('treats unavailable storage as already booted', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const el = mount();
    initBootscreen(el);
    expect(el.isConnected).toBe(false);
  });

  it('never runs with reduced motion', () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (q: string) => ({ matches: q.includes('reduce'), media: q }) as unknown as MediaQueryList,
    );
    const el = mount();
    initBootscreen(el);
    expect(el.isConnected).toBe(false);
    expect(sessionStorage.getItem(BOOT_KEY)).toBeNull();
  });

  it('any key skips straight to the exit', () => {
    vi.useFakeTimers();
    const el = mount();
    initBootscreen(el);
    vi.advanceTimersByTime(100);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'x' }));
    expect(el.classList.contains('fx-boot--out')).toBe(true);
    vi.advanceTimersByTime(400);
    expect(el.isConnected).toBe(false);
    expect(document.documentElement.dataset.booting).toBeUndefined();
  });
});
