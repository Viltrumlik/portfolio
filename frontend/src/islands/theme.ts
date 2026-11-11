export type Theme = 'dark' | 'light';

export function themeCookie(theme: Theme): string {
  return `theme=${theme}; path=/; max-age=31536000; samesite=lax`;
}

/** Pulse (dark) is the default: anything but "light" reads as dark. */
export function currentTheme(root: HTMLElement = document.documentElement): Theme {
  return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

export function setTheme(theme: Theme, root: HTMLElement = document.documentElement): Theme {
  const doc = root.ownerDocument;
  root.setAttribute('data-theme', theme);
  doc.cookie = themeCookie(theme);
  doc.dispatchEvent(new CustomEvent('atlas:themechange', { detail: { theme } }));
  return theme;
}

export function toggleTheme(root: HTMLElement = document.documentElement): Theme {
  return setTheme(currentTheme(root) === 'dark' ? 'light' : 'dark', root);
}

/** Delegated: any click inside a [data-theme-toggle] flips the theme. Returns an unsubscribe. */
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
