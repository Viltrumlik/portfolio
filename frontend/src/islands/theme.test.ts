import { afterEach, describe, expect, it, vi } from 'vitest';
import { THEMES, currentTheme, initThemeToggles, setTheme, themeCookie, toggleTheme } from './theme';

afterEach(() => {
  document.documentElement.removeAttribute('data-theme');
  document.cookie = 'theme=; path=/; max-age=0';
  document.body.innerHTML = '';
});

describe('themeCookie', () => {
  it('is a one-year, site-wide, lax cookie', () => {
    expect(themeCookie('amber')).toBe('theme=amber; path=/; max-age=31536000; samesite=lax');
  });
});

describe('theme', () => {
  it('cycles through the three phosphor themes, green first', () => {
    expect(THEMES).toEqual(['green', 'amber', 'ice']);
  });

  it('treats a missing, unknown or legacy data-theme as green (the default)', () => {
    expect(currentTheme(document.documentElement)).toBe('green');
    for (const legacy of ['sepia', 'dark', 'light']) {
      document.documentElement.setAttribute('data-theme', legacy);
      expect(currentTheme(document.documentElement)).toBe('green');
    }
  });

  it('setTheme writes data-theme and the cookie', () => {
    setTheme('ice');
    expect(document.documentElement.getAttribute('data-theme')).toBe('ice');
    expect(document.cookie).toContain('theme=ice');
  });

  it('toggleTheme cycles green -> amber -> ice -> green and returns the new theme', () => {
    document.documentElement.setAttribute('data-theme', 'green');
    expect(toggleTheme()).toBe('amber');
    expect(toggleTheme()).toBe('ice');
    expect(toggleTheme()).toBe('green');
    expect(document.documentElement.dataset.theme).toBe('green');
    expect(document.cookie).toContain('theme=green');
  });

  it('announces the change with an atlas:themechange event', () => {
    const seen = vi.fn();
    document.addEventListener('atlas:themechange', (e) => seen((e as CustomEvent).detail));
    setTheme('amber');
    expect(seen).toHaveBeenCalledWith({ theme: 'amber' });
  });

  it('advances the theme when any [data-theme-toggle] (or its child) is clicked', () => {
    document.documentElement.setAttribute('data-theme', 'green');
    document.body.innerHTML = '<button data-theme-toggle><span id="inner">Theme</span></button>';
    const stop = initThemeToggles(document);
    document.getElementById('inner')!.click();
    expect(document.documentElement.dataset.theme).toBe('amber');
    stop();
    document.getElementById('inner')!.click();
    expect(document.documentElement.dataset.theme).toBe('amber');
  });
});
