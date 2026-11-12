// Matrix effects for Atlas v3. Islands are registered by boot.ts; initSiteFx wires the
// document-level effects (cursor trail, sound) on public pages only.

import { initBootscreen } from './bootscreen';
import { initDecode } from './decode';
import { initRain } from './rain';
import { initSound } from './sound';
import { initCursorTrail } from './trail';
import { initTyper } from './typer';

export const FX_ISLANDS: Record<string, (el: HTMLElement) => unknown> = {
  rain: (el) => (el instanceof el.ownerDocument.defaultView!.HTMLCanvasElement ? initRain(el) : null),
  decode: initDecode,
  typer: initTyper,
  bootscreen: initBootscreen,
};

const wired = new WeakSet<Document>();

export function initSiteFx(doc: Document = document): void {
  if (!doc.body?.classList.contains('at-site') || wired.has(doc)) return;
  wired.add(doc);
  initSound(doc);
  initCursorTrail(doc);
}
