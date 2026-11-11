// Desk island: drag windows by their title bars inside an .at-desk (vanilla, no framework).

export interface Point {
  x: number;
  y: number;
}
export interface Size {
  width: number;
  height: number;
}

const CONTROLS = 'a, button, input, select, textarea, label, [role="button"], [data-no-drag]';

/** Keep a window of size `win` fully inside a desk of size `desk` (top-left wins if it can't fit). */
export function clampPosition(pos: Point, win: Size, desk: Size): Point {
  const clamp = (v: number, max: number) => Math.max(0, Math.min(max, v));
  return { x: clamp(pos.x, desk.width - win.width), y: clamp(pos.y, desk.height - win.height) };
}

/** Stacking order is bottom -> top; returns a new order with `id` on top. */
export function bringToFront(order: readonly string[], id: string): string[] {
  if (!order.includes(id)) return [...order];
  return [...order.filter((x) => x !== id), id];
}

/**
 * Dragging follows the CSS layout instead of repeating its breakpoint: windows are draggable only while
 * they are absolutely placed on the desk. The stacked desk (site.css, under 1024px) makes them static.
 */
export function isDraggable(win: HTMLElement): boolean {
  const view = win.ownerDocument.defaultView;
  return !!view && view.getComputedStyle(win).position === 'absolute';
}

export function initDesk(desk: HTMLElement): () => void {
  const doc = desk.ownerDocument;
  const windows = () => Array.from(desk.querySelectorAll<HTMLElement>(':scope > .at-win[data-win]'));
  let order = windows().map((w) => w.dataset.win!);

  const paintStack = () => {
    const els = windows();
    order.forEach((id, i) => {
      const el = els.find((w) => w.dataset.win === id);
      if (el) el.style.zIndex = String(i + 1);
    });
  };
  paintStack();

  let endDrag: (() => void) | null = null;

  const onPointerDown = (e: PointerEvent) => {
    if (e.button !== 0) return;
    const target = e.target as Element;
    const bar = target.closest<HTMLElement>('.at-win__bar');
    const win = bar?.parentElement;
    if (!bar || !win || win.parentElement !== desk || !win.dataset.win) return;
    if (target.closest(CONTROLS)) return;

    const id = win.dataset.win;
    order = bringToFront(order, id);
    paintStack();
    for (const w of windows()) w.classList.toggle('is-active', w === win);

    if (!isDraggable(win)) return;
    e.preventDefault();
    endDrag?.();

    // Layout boxes, not getBoundingClientRect() of the window: its hover/drag transforms would shift the grab point.
    const deskRect = desk.getBoundingClientRect();
    const origin = { x: deskRect.left + desk.clientLeft, y: deskRect.top + desk.clientTop };
    const deskSize = { width: desk.clientWidth, height: desk.clientHeight };
    const winSize = { width: win.offsetWidth, height: win.offsetHeight };
    const offset = { x: e.clientX - origin.x - win.offsetLeft, y: e.clientY - origin.y - win.offsetTop };
    try {
      bar.setPointerCapture?.(e.pointerId);
    } catch {
      /* synthetic or already-released pointer */
    }
    win.classList.add('is-dragging');

    const onMove = (ev: PointerEvent) => {
      const p = clampPosition({ x: ev.clientX - origin.x - offset.x, y: ev.clientY - origin.y - offset.y }, winSize, deskSize);
      win.style.setProperty('--x', `${Math.round(p.x)}px`);
      win.style.setProperty('--y', `${Math.round(p.y)}px`);
    };
    const onUp = () => {
      win.classList.remove('is-dragging');
      doc.removeEventListener('pointermove', onMove);
      doc.removeEventListener('pointerup', onUp);
      doc.removeEventListener('pointercancel', onUp);
      endDrag = null;
    };
    doc.addEventListener('pointermove', onMove);
    doc.addEventListener('pointerup', onUp);
    doc.addEventListener('pointercancel', onUp);
    endDrag = onUp;
  };

  desk.addEventListener('pointerdown', onPointerDown as EventListener);
  return () => {
    endDrag?.();
    desk.removeEventListener('pointerdown', onPointerDown as EventListener);
  };
}
