// Main-chunk side of the command palette: listens for ⌘K / Ctrl+K and [data-cmdk-open] clicks,
// and imports the Preact palette chunk on first use. Must not import preact.
import { toggleTheme } from '../islands/theme';
import type { OpenOptions } from './mount';

interface PaletteModule {
  openPalette: (options: OpenOptions) => void;
}
export type PaletteLoader = () => Promise<PaletteModule>;

const loadPalette: PaletteLoader = () => import('./mount');

export function initCommandPalette(doc: Document = document, load: PaletteLoader = loadPalette): () => void {
  let pending: Promise<PaletteModule> | null = null;
  const hasData = () => doc.getElementById('atlas-cmdk') !== null;

  const open = () => {
    pending ??= load().catch((err: unknown) => {
      pending = null; // allow a retry after a failed chunk load
      throw err;
    });
    pending
      .then((m) => m.openPalette({ toggleTheme: () => toggleTheme(doc.documentElement), doc }))
      .catch(() => {});
  };

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.isComposing || !(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return;
    if (e.key.toLowerCase() !== 'k' || !hasData()) return;
    e.preventDefault();
    open();
  };
  const onClick = (e: MouseEvent) => {
    const trigger = (e.target as Element | null)?.closest?.('[data-cmdk-open]');
    if (!trigger || !hasData()) return;
    e.preventDefault();
    open();
  };

  doc.addEventListener('keydown', onKeyDown);
  doc.addEventListener('click', onClick);
  return () => {
    doc.removeEventListener('keydown', onKeyDown);
    doc.removeEventListener('click', onClick);
  };
}
