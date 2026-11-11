import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { bringToFront, clampPosition, initDesk } from './desk';

describe('clampPosition', () => {
  const desk = { width: 1000, height: 520 };
  const win = { width: 400, height: 200 };

  it('keeps a position that already fits', () => {
    expect(clampPosition({ x: 100, y: 50 }, win, desk)).toEqual({ x: 100, y: 50 });
  });

  it('clamps to the top-left corner', () => {
    expect(clampPosition({ x: -30, y: -1 }, win, desk)).toEqual({ x: 0, y: 0 });
  });

  it('clamps to the bottom-right corner so the window stays inside', () => {
    expect(clampPosition({ x: 900, y: 600 }, win, desk)).toEqual({ x: 600, y: 320 });
  });

  it('pins a window larger than the desk to 0', () => {
    expect(clampPosition({ x: 50, y: 50 }, { width: 1200, height: 900 }, desk)).toEqual({ x: 0, y: 0 });
  });
});

describe('bringToFront', () => {
  it('moves the id to the top of the stacking order', () => {
    expect(bringToFront(['a', 'b', 'c'], 'a')).toEqual(['b', 'c', 'a']);
  });

  it('is a no-op for the window already on top', () => {
    expect(bringToFront(['a', 'b', 'c'], 'c')).toEqual(['a', 'b', 'c']);
  });

  it('ignores unknown ids and never mutates the input', () => {
    const order = ['a', 'b'];
    expect(bringToFront(order, 'zzz')).toEqual(['a', 'b']);
    bringToFront(order, 'a');
    expect(order).toEqual(['a', 'b']);
  });
});

function rect(left: number, top: number, width: number, height: number): DOMRect {
  return { left, top, width, height, right: left + width, bottom: top + height, x: left, y: top, toJSON() {} } as DOMRect;
}

function pointer(type: string, init: { clientX?: number; clientY?: number; button?: number }) {
  return new MouseEvent(type, { bubbles: true, cancelable: true, button: 0, ...init });
}

describe('initDesk', () => {
  let desk: HTMLElement;
  const win = (id: string) => desk.querySelector<HTMLElement>(`[data-win="${id}"]`)!;
  const bar = (id: string) => win(id).querySelector<HTMLElement>('.at-win__bar')!;
  // Stand-in for site.css: windows are absolutely placed on a wide desk, static when the desk is stacked.
  const layout = document.createElement('style');

  beforeEach(() => {
    // matchMedia must not decide anything any more: say "small screen" to prove it is ignored.
    vi.stubGlobal('matchMedia', (q: string) => ({ matches: true, media: q }));
    layout.textContent = '.at-desk > .at-win { position: absolute; } .at-desk.is-stacked > .at-win { position: static; }';
    document.head.appendChild(layout);
    document.body.innerHTML = `
      <div class="at-desk" data-island="desk">
        <section class="at-win is-active" data-win="about" style="--x:3%;--y:20px;--w:46%">
          <div class="at-win__bar"><span class="at-win__title">about.md</span><span class="at-win__end"><button id="btn">x</button></span></div>
          <div class="at-win__body">hi</div>
        </section>
        <section class="at-win" data-win="now" style="--x:52%;--y:40px;--w:30%">
          <div class="at-win__bar"><span class="at-win__title">now.app</span></div>
        </section>
        <section class="at-win" data-win="github" style="--x:60%;--y:260px;--w:34%">
          <div class="at-win__bar"><span class="at-win__title">github.app</span></div>
        </section>
      </div>`;
    desk = document.querySelector('.at-desk')!;
    desk.getBoundingClientRect = () => rect(100, 50, 1000, 520);
    define(desk, { clientWidth: 1000, clientHeight: 520, clientLeft: 0, clientTop: 0 });
    // Layout box (untransformed) of "now" inside the desk: 520,40 300x200.
    define(win('now'), { offsetLeft: 520, offsetTop: 40, offsetWidth: 300, offsetHeight: 200 });
    // The hover lift (translate -3px) shows up in the visual rect only; it must not shift the drag.
    win('now').getBoundingClientRect = () => rect(617, 87, 300, 200);
  });

  function define(el: HTMLElement, props: Record<string, number>) {
    for (const [k, v] of Object.entries(props)) Object.defineProperty(el, k, { value: v, configurable: true });
  }

  afterEach(() => {
    vi.unstubAllGlobals();
    layout.remove();
    document.body.innerHTML = '';
  });

  it('stacks windows in DOM order on init', () => {
    initDesk(desk);
    expect(win('about').style.zIndex).toBe('1');
    expect(win('now').style.zIndex).toBe('2');
    expect(win('github').style.zIndex).toBe('3');
  });

  it('brings a pressed window to the front and makes it the only active one', () => {
    initDesk(desk);
    bar('now').dispatchEvent(pointer('pointerdown', { clientX: 640, clientY: 100 }));
    expect(win('now').classList.contains('is-active')).toBe(true);
    expect(win('about').classList.contains('is-active')).toBe(false);
    expect(win('github').classList.contains('is-active')).toBe(false);
    expect(Number(win('now').style.zIndex)).toBeGreaterThan(Number(win('github').style.zIndex));
    expect(Number(win('github').style.zIndex)).toBeGreaterThan(Number(win('about').style.zIndex));
  });

  it('drags by the bar, writing clamped --x/--y in px, with is-dragging only during the drag', () => {
    initDesk(desk);
    // Grab 20px right / 10px below the window's top-left corner (window at desk-relative 520,40).
    bar('now').dispatchEvent(pointer('pointerdown', { clientX: 640, clientY: 100 }));
    expect(win('now').classList.contains('is-dragging')).toBe(true);

    document.dispatchEvent(pointer('pointermove', { clientX: 400, clientY: 300 }));
    expect(win('now').style.getPropertyValue('--x')).toBe('280px');
    expect(win('now').style.getPropertyValue('--y')).toBe('240px');

    // Far past the bottom-right corner: clamped to desk - window.
    document.dispatchEvent(pointer('pointermove', { clientX: 5000, clientY: 5000 }));
    expect(win('now').style.getPropertyValue('--x')).toBe('700px');
    expect(win('now').style.getPropertyValue('--y')).toBe('320px');

    document.dispatchEvent(pointer('pointerup', {}));
    expect(win('now').classList.contains('is-dragging')).toBe(false);

    document.dispatchEvent(pointer('pointermove', { clientX: 300, clientY: 300 }));
    expect(win('now').style.getPropertyValue('--x')).toBe('700px');
  });

  it('does not drag while CSS stacks the desk (windows not absolutely positioned) but still activates', () => {
    desk.classList.add('is-stacked');
    initDesk(desk);
    bar('now').dispatchEvent(pointer('pointerdown', { clientX: 640, clientY: 100 }));
    expect(win('now').classList.contains('is-active')).toBe(true);
    expect(win('now').classList.contains('is-dragging')).toBe(false);
    document.dispatchEvent(pointer('pointermove', { clientX: 400, clientY: 300 }));
    expect(win('now').style.getPropertyValue('--x')).toBe('52%');
  });

  it('ignores secondary buttons and presses on controls inside the bar', () => {
    initDesk(desk);
    bar('now').dispatchEvent(pointer('pointerdown', { clientX: 640, clientY: 100, button: 2 }));
    expect(win('now').classList.contains('is-active')).toBe(false);
    document.getElementById('btn')!.dispatchEvent(pointer('pointerdown', { clientX: 10, clientY: 10 }));
    expect(win('about').classList.contains('is-dragging')).toBe(false);
  });
});
