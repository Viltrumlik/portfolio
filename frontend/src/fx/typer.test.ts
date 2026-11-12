import { afterEach, describe, expect, it, vi } from 'vitest';
import { initTyper } from './typer';

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

const TRANSCRIPT = '$ whoami\nviltrumlik\n$ uptime\nup 412 days';

function mount(attrs = '') {
  document.body.innerHTML = `<pre data-island="typer" ${attrs}>${TRANSCRIPT}</pre>`;
  return document.querySelector<HTMLElement>('pre')!;
}

const screen = (el: HTMLElement) => el.querySelector<HTMLElement>('.fx-typer-screen')!;

describe('initTyper', () => {
  it('keeps the full transcript for screen readers and hides the animated copy', () => {
    vi.useFakeTimers();
    const el = mount();
    initTyper(el);
    expect(el.querySelector('.fx-sr')!.textContent).toBe(TRANSCRIPT);
    expect(screen(el).getAttribute('aria-hidden')).toBe('true');
    expect(el.querySelector('.fx-cursor')).not.toBeNull();
  });

  it('types commands character by character', () => {
    vi.useFakeTimers();
    const el = mount();
    initTyper(el);
    vi.advanceTimersByTime(45 * 3 + 5);
    const text = screen(el).textContent!;
    expect(text.startsWith('$ w')).toBe(true);
    expect(text.length).toBeLessThan('$ whoami'.length);
  });

  it('ends with the whole transcript', () => {
    vi.useFakeTimers();
    const el = mount();
    initTyper(el);
    vi.advanceTimersByTime(10_000);
    expect(screen(el).textContent).toBe(TRANSCRIPT);
  });

  it('caps the visible lines', () => {
    vi.useFakeTimers();
    const el = mount('data-max-lines="2"');
    initTyper(el);
    vi.advanceTimersByTime(10_000);
    expect(screen(el).textContent).toBe('$ uptime\nup 412 days');
  });

  it('loops after the pause', () => {
    vi.useFakeTimers();
    const el = mount('data-loop="1000"');
    initTyper(el);
    vi.advanceTimersByTime(1_500);
    expect(screen(el).textContent).toBe(TRANSCRIPT);
    vi.advanceTimersByTime(1_000 + 100);
    expect(screen(el).textContent!.length).toBeLessThan(TRANSCRIPT.length);
  });

  it('stop() halts typing', () => {
    vi.useFakeTimers();
    const el = mount();
    const t = initTyper(el)!;
    vi.advanceTimersByTime(100);
    t.stop();
    const snap = screen(el).textContent;
    vi.advanceTimersByTime(5_000);
    expect(screen(el).textContent).toBe(snap);
  });

  it('leaves the static transcript under reduced motion', () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (q: string) => ({ matches: q.includes('reduce'), media: q }) as unknown as MediaQueryList,
    );
    const el = mount();
    expect(initTyper(el)).toBeNull();
    expect(el.textContent).toBe(TRANSCRIPT);
    expect(el.querySelector('.fx-typer-screen')).toBeNull();
  });
});
