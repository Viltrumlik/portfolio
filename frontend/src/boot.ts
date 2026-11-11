import { initCommandPalette } from './cmdk/trigger';
import { initClock } from './islands/clock';
import { initDesk } from './islands/desk';
import { initNow } from './islands/now';
import { initTemplatePreview } from './islands/template-preview';
import { initThemeToggles } from './islands/theme';

/** data-island="<name>" -> initialiser. Each runs once per element. */
const ISLANDS: Record<string, (el: HTMLElement) => unknown> = {
  desk: initDesk,
  clock: initClock,
  now: initNow,
  'template-preview': initTemplatePreview,
};

const wiredDocs = new WeakSet<Document>();

export function boot(doc: Document = document): void {
  if (!wiredDocs.has(doc)) {
    wiredDocs.add(doc);
    initThemeToggles(doc);
    initCommandPalette(doc);
  }
  for (const el of doc.querySelectorAll<HTMLElement>('[data-island]')) {
    const init = ISLANDS[el.dataset.island ?? ''];
    if (!init || el.hasAttribute('data-island-ready')) continue;
    el.setAttribute('data-island-ready', '');
    try {
      init(el);
    } catch (err) {
      console.error(`[atlas] island "${el.dataset.island}" failed`, err);
    }
  }
}
