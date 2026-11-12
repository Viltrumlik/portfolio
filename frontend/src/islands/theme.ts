/** Phosphor themes, in toggle order. Green is the default. */
export const THEMES = ['green', 'amber', 'ice'] as const;
export type Theme = (typeof THEMES)[number];

export function themeCookie(theme: Theme): string {
  return `theme=${theme}; path=/; max-age=31536000; samesite=lax`;
}

function isTheme(value: string | null): value is Theme {
  return (THEMES as readonly string[]).includes(value ?? '');
}

/** Anything that is not a known phosphor theme (including the old dark/light) reads as green. */
export function currentTheme(root: HTMLElement = document.documentElement): Theme {
  const value = root.getAttribute('data-theme');
  return isTheme(value) ? value : 'green';
}

export function setTheme(theme: Theme, root: HTMLElement = document.documentElement): Theme {
  const doc = root.ownerDocument;
  root.setAttribute('data-theme', theme);
  doc.cookie = themeCookie(theme);
  doc.dispatchEvent(new CustomEvent('atlas:themechange', { detail: { theme } }));
  return theme;
}

/** Advance to the next phosphor: green -> amber -> ice -> green. */
export function toggleTheme(root: HTMLElement = document.documentElement): Theme {
  const next = THEMES[(THEMES.indexOf(currentTheme(root)) + 1) % THEMES.length];
  return setTheme(next, root);
}

/** Delegated: any click inside a [data-theme-toggle] advances the theme. Returns an unsubscribe. */
export function initThemeToggles(doc: Document = document): () => void {
  const onClick = (e: Event) => {
    const target = e.target as Element | null;
    if (!target?.closest?.('[data-theme-toggle]')) return;
    e.preventDefault();
    toggleTheme(doc.documentElement);
  };
  doc.addEventListener('click', onClick);
  return () => doc.removeEventListener('click', onClick);
}
