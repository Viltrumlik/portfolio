import { afterEach, describe, expect, it, vi } from 'vitest';
import { boot } from './boot';

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
  document.documentElement.removeAttribute('data-theme');
});

describe('boot', () => {
  it('initialises every known island found in the DOM, once', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    document.body.innerHTML = `
      <time data-island="clock" data-tz="UTC" data-format="HH:MM">--:--</time>
      <div data-island="template-preview" data-sample='{"repo":"r"}'>
        <textarea data-template-input>{{repo}}!</textarea><p data-template-output></p>
      </div>
      <section data-island="now" data-src="/api/live/now.json"></section>
      <div class="at-desk" data-island="desk"><section class="at-win" data-win="a"><div class="at-win__bar"></div></section></div>
      <div data-island="unknown-thing"></div>`;
    boot(document);
    boot(document);
    expect(document.querySelector('time')!.textContent).toMatch(/^\d\d:\d\d$/);
    expect(document.querySelector('[data-template-output]')!.textContent).toBe('r!');
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(document.querySelector<HTMLElement>('[data-win="a"]')!.style.zIndex).toBe('1');
    expect(document.querySelector('[data-island="clock"]')!.hasAttribute('data-island-ready')).toBe(true);
    expect(document.querySelector('[data-island="unknown-thing"]')!.hasAttribute('data-island-ready')).toBe(false);
  });

  it('wires the theme toggles once even when booted twice', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.body.innerHTML = '<button data-theme-toggle>theme</button>';
    boot(document);
    boot(document);
    document.querySelector<HTMLElement>('[data-theme-toggle]')!.click();
    expect(document.documentElement.dataset.theme).toBe('light');
  });

  it('keeps going when one island throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    document.body.innerHTML = `
      <div data-island="template-preview" data-sample='{"a":1}'>
        <textarea data-template-input>{{a}}</textarea><p data-template-output></p>
      </div>`;
    const area = document.querySelector('textarea')!;
    Object.defineProperty(area, 'value', { get: () => { throw new Error('boom'); } });
    document.body.insertAdjacentHTML('beforeend', '<time data-island="clock" data-tz="UTC"></time>');
    expect(() => boot(document)).not.toThrow();
    expect(document.querySelector('time')!.textContent).toMatch(/^\d\d:\d\d$/);
  });
});
