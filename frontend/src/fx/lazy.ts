// Eager shim for the effects: the boot screen runs at once (it must cover the page before first
// paint settles); everything else loads in a separate chunk on first use.

import { initBootscreen } from './bootscreen';

type FxModule = typeof import('./index');
type Init = (el: HTMLElement) => unknown;

export const loadFx = (): Promise<FxModule> => import('./index');

const deferred =
  (name: 'rain' | 'decode' | 'typer'): Init =>
  (el) =>
    loadFx()
      .then((fx) => fx.FX_ISLANDS[name](el))
      .catch((err) => console.error(`[atlas] fx "${name}" failed to load`, err));

export const LAZY_FX_ISLANDS: Record<string, Init> = {
  rain: deferred('rain'),
  decode: deferred('decode'),
  typer: deferred('typer'),
  bootscreen: initBootscreen,
};

/** Cursor trail and sound, loaded only on public pages (body.at-site). */
export function initSiteFxLazy(doc: Document = document, load: () => Promise<FxModule> = loadFx): void {
  if (!doc.body?.classList.contains('at-site')) return;
  load()
    .then((fx) => fx.initSiteFx(doc))
    .catch((err) => console.error('[atlas] site fx failed to load', err));
}
