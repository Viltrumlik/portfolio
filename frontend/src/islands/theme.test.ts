import { afterEach, describe, expect, it, vi } from 'vitest';
import { currentTheme, initThemeToggles, setTheme, themeCookie, toggleTheme } from './theme';

afterEach(() => {
  document.documentElement.removeAttribute('data-theme');
  document.cookie = 'theme=; path=/; max-age=0';
  document.body.innerHTML = '';
});

describe('themeCookie', () => {
  it('is a one-year, site-wide, lax cookie', () => {
    expect(themeCookie('light')).toBe('theme=light; path=/; max-age=31536000; samesite=lax');
  });
});

describe('theme', () => {
  it('treats a missing or unknown data-theme as dark (Pulse is the default)', () => {
    expect(currentTheme(document.documentElement)).toBe('dark');
    document.documentElement.setAttribute('data-theme', 'sepia');
    expect(currentTheme(document.documentElement)).toBe('dark');
  });

  it('setTheme writes data-theme and the cookie', () => {
    setTheme('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(document.cookie).toContain('theme=light');
  });

  it('toggleTheme flips dark -> light -> dark and returns the new theme', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    expect(toggleTheme()).toBe('light');
    expect(document.documentElement.dataset.theme).toBe('light');
    expect(toggleTheme()).toBe('dark');
    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(document.cookie).toContain('theme=dark');
  });

  it('announces the change with an atlas:themechange event', () => {
    const seen = vi.fn();
    document.addEventListener('atlas:themechange', (e) => seen((e as CustomEvent).detail));
    setTheme('light');
    expect(seen).toHaveBeenCalledWith({ theme: 'light' });
  });

  it('flips the theme when any [data-theme-toggle] (or its child) is clicked', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.body.innerHTML = '<button data-theme-toggle><span id="inner">Theme</span></button>';
    const stop = initThemeToggles(document);
    document.getElementById('inner')!.click();
    expect(document.documentElement.dataset.theme).toBe('light');
    stop();
    document.getElementById('inner')!.click();
    expect(document.documentElement.dataset.theme).toBe('light');
  });
});
