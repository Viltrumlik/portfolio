// Lazily loaded chunk: renders the CommandPalette in a dimmed overlay appended to <body>.
import { render } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { CommandPalette } from './CommandPalette';
import type { CommandGroup, CommandItem } from './types';

export interface OpenOptions {
  toggleTheme: () => unknown;
  navigate?: (href: string) => void;
  doc?: Document;
}

const COPIED_MS = 900;

interface OpenState {
  doc: Document;
  container: HTMLElement;
  restore: HTMLElement | null;
  overflow: string;
  detach: () => void;
}

let open: OpenState | null = null;

export function isPaletteOpen(): boolean {
  return open !== null;
}

export function readCommandGroups(doc: Document): CommandGroup[] {
  try {
    const data = JSON.parse(doc.getElementById('atlas-cmdk')?.textContent || '');
    return Array.isArray(data?.groups) ? data.groups : [];
  } catch {
    return [];
  }
}

export async function copyText(text: string, doc: Document): Promise<boolean> {
  try {
    await doc.defaultView!.navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Insecure context or no permission: fall back to a hidden textarea.
    const ta = doc.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
    doc.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = doc.execCommand('copy');
    } catch {
      ok = false;
    }
    ta.remove();
    return ok;
  }
}

function inputOf(container: HTMLElement) {
  return container.querySelector<HTMLInputElement>('.at-cmd__input');
}

function Palette({ groups, options, doc }: { groups: CommandGroup[]; options: OpenOptions; doc: Document }) {
  const [flash, setFlash] = useState<{ item: CommandItem; text: string } | null>(null);
  const [status, setStatus] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => () => clearTimeout(timer.current), []);

  const onSelect = (item: CommandItem) => {
    const action = item.action ?? '';
    if (item.href) {
      closePalette();
      (options.navigate ?? ((href: string) => doc.defaultView!.location.assign(href)))(item.href);
    } else if (action === 'theme') {
      options.toggleTheme();
      closePalette();
    } else if (action.startsWith('copy:')) {
      void copyText(action.slice('copy:'.length), doc).then((ok) => {
        if (!isPaletteOpen()) return;
        setFlash({ item, text: ok ? 'Copied' : 'Copy failed' });
        setStatus(ok ? 'Copied to clipboard' : 'Could not copy');
        clearTimeout(timer.current);
        timer.current = setTimeout(closePalette, COPIED_MS);
      });
    }
  };

  return (
    <>
      <CommandPalette groups={groups} onSelect={onSelect} onClose={closePalette} flash={flash} autoFocus modal />
      <p class="at-sr" role="status" aria-live="polite">
        {status}
      </p>
    </>
  );
}

export function openPalette(options: OpenOptions): void {
  const doc = options.doc ?? document;
  if (open) {
    inputOf(open.container)?.focus();
    return;
  }

  const container = doc.createElement('div');
  container.className = 'at-cmdk';
  doc.body.appendChild(container);

  const refocus = () => inputOf(container)?.focus();
  const onClick = (e: MouseEvent) => {
    if (e.target === container) closePalette();
  };
  const onMouseDown = (e: MouseEvent) => {
    // Keep focus in the input while clicking rows or the backdrop.
    if (!(e.target as Element).closest('.at-cmd__input')) e.preventDefault();
  };
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      refocus();
    } else if (e.key === 'Escape' && !e.defaultPrevented) {
      closePalette();
    }
  };
  const onFocusIn = (e: FocusEvent) => {
    if (open && !container.contains(e.target as Node)) refocus();
  };
  container.addEventListener('click', onClick);
  container.addEventListener('mousedown', onMouseDown);
  container.addEventListener('keydown', onKeyDown);
  doc.addEventListener('focusin', onFocusIn);

  open = {
    doc,
    container,
    restore: doc.activeElement instanceof HTMLElement ? doc.activeElement : null,
    overflow: doc.documentElement.style.overflow,
    detach: () => {
      container.removeEventListener('click', onClick);
      container.removeEventListener('mousedown', onMouseDown);
      container.removeEventListener('keydown', onKeyDown);
      doc.removeEventListener('focusin', onFocusIn);
    },
  };
  doc.documentElement.style.overflow = 'hidden';
  render(<Palette groups={readCommandGroups(doc)} options={options} doc={doc} />, container);
  refocus();
}

export function closePalette(): void {
  if (!open) return;
  const { doc, container, restore, overflow, detach } = open;
  open = null;
  detach();
  render(null, container);
  container.remove();
  doc.documentElement.style.overflow = overflow;
  if (restore?.isConnected) restore.focus();
}
