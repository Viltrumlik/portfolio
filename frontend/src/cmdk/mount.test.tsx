import { act } from 'preact/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { groups } from './fixtures';
import { closePalette, isPaletteOpen, openPalette, type OpenOptions } from './mount';

const overlay = () => document.querySelector<HTMLElement>('.at-cmdk');
const input = () => document.querySelector<HTMLInputElement>('.at-cmdk .at-cmd__input')!;
const optionLabels = () => Array.from(document.querySelectorAll('.at-cmdk [role="option"] .at-cmd__label')).map((o) => o.textContent);

function key(k: string, target: Element = input()) {
  const ev = new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true });
  act(() => {
    target.dispatchEvent(ev);
  });
  return ev;
}

function type(text: string) {
  act(() => {
    input().value = text;
    input().dispatchEvent(new Event('input', { bubbles: true }));
  });
}

let opts: OpenOptions & { toggleTheme: ReturnType<typeof vi.fn>; navigate: ReturnType<typeof vi.fn> };
let writeText: ReturnType<typeof vi.fn>;

function open(extra: Partial<OpenOptions> = {}) {
  act(() => {
    openPalette({ ...opts, ...extra });
  });
}

beforeEach(() => {
  document.body.innerHTML = `
    <button id="trigger" data-cmdk-open>Search</button>
    <script type="application/json" id="atlas-cmdk">${JSON.stringify({ groups })}</script>`;
  document.getElementById('trigger')!.focus();
  opts = { toggleTheme: vi.fn(), navigate: vi.fn() };
  writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
});

afterEach(() => {
  act(() => closePalette());
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('openPalette', () => {
  it('renders the palette from #atlas-cmdk in an overlay appended to body and focuses the input', () => {
    open();
    expect(isPaletteOpen()).toBe(true);
    expect(overlay()!.parentElement).toBe(document.body);
    expect(overlay()!.querySelector('section.at-win.at-cmd[role="dialog"]')!.getAttribute('aria-modal')).toBe('true');
    expect(optionLabels()).toEqual(['Home', 'Projects', 'Switch to the Sage theme', 'Copy email']);
    expect(document.activeElement).toBe(input());
  });

  it('opens only once', () => {
    open();
    open();
    expect(document.querySelectorAll('.at-cmdk')).toHaveLength(1);
  });

  it('closes on Escape and restores focus to the element focused before opening', () => {
    open();
    key('Escape');
    expect(overlay()).toBeNull();
    expect(isPaletteOpen()).toBe(false);
    expect(document.activeElement).toBe(document.getElementById('trigger'));
  });

  it('closes on a click on the dimmed backdrop, not inside the window', () => {
    open();
    act(() => {
      overlay()!.querySelector('.at-cmd__list')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(overlay()).not.toBeNull();
    act(() => {
      overlay()!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(overlay()).toBeNull();
  });

  it('traps focus in the input: Tab is swallowed and focus returns if it escapes', () => {
    open();
    expect(key('Tab').defaultPrevented).toBe(true);
    expect(key('Tab', overlay()!).defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(input());
    act(() => {
      document.getElementById('trigger')!.focus();
    });
    expect(document.activeElement).toBe(input());
  });

  it('locks page scroll while open', () => {
    document.documentElement.style.overflow = 'auto';
    open();
    expect(document.documentElement.style.overflow).toBe('hidden');
    act(() => closePalette());
    expect(document.documentElement.style.overflow).toBe('auto');
  });

  it('navigates to an item href and closes', () => {
    open();
    key('Enter');
    expect(opts.navigate).toHaveBeenCalledWith('/');
    expect(overlay()).toBeNull();
  });

  it('runs the theme action and closes', () => {
    open();
    type('sage');
    key('Enter');
    expect(opts.toggleTheme).toHaveBeenCalledTimes(1);
    expect(opts.navigate).not.toHaveBeenCalled();
    expect(overlay()).toBeNull();
  });

  it('copies "copy:<text>" to the clipboard, shows Copied, then closes', async () => {
    vi.useFakeTimers();
    open();
    type('email');
    await act(async () => {
      input().dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
      for (let i = 0; i < 5; i++) await Promise.resolve();
    });
    expect(writeText).toHaveBeenCalledWith('me@example.com');
    expect(document.querySelector('.at-cmdk .at-cmd__item.is-active .at-cmd__hint')!.textContent).toBe('Copied');
    expect(document.querySelector('.at-cmdk [role="status"]')!.textContent).toBe('Copied to clipboard');
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(overlay()).toBeNull();
  });

  it('opens with no items when the data script is missing or invalid', () => {
    document.getElementById('atlas-cmdk')!.textContent = '{nope';
    expect(() => open()).not.toThrow();
    expect(optionLabels()).toEqual([]);
  });
});
