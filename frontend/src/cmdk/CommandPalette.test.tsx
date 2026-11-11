import { render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommandPalette, type CommandPaletteProps } from './CommandPalette';
import { groups } from './fixtures';

let root: HTMLElement;

function setup(props: Partial<CommandPaletteProps> = {}) {
  const onSelect = vi.fn();
  const onClose = vi.fn();
  root = document.createElement('div');
  document.body.appendChild(root);
  act(() => {
    render(<CommandPalette groups={groups} onSelect={onSelect} onClose={onClose} autoFocus {...props} />, root);
  });
  return { onSelect, onClose };
}

const input = () => root.querySelector<HTMLInputElement>('input.at-cmd__input')!;
const options = () => Array.from(root.querySelectorAll<HTMLElement>('[role="option"]'));
const activeLabel = () => root.querySelector('.at-cmd__item.is-active .at-cmd__label')?.textContent;

function key(k: string) {
  const ev = new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true });
  act(() => {
    input().dispatchEvent(ev);
  });
  return ev;
}

function type(text: string) {
  act(() => {
    input().value = text;
    input().dispatchEvent(new Event('input', { bubbles: true }));
  });
}

afterEach(() => {
  render(null, root);
  root.remove();
});

describe('CommandPalette', () => {
  it('renders as an active Atlas window dialog with grouped options', () => {
    setup();
    const win = root.querySelector('section.at-win.at-cmd')!;
    expect(win.classList.contains('is-active')).toBe(true);
    expect(win.getAttribute('role')).toBe('dialog');
    expect(win.getAttribute('aria-label')).toBe('Command palette');
    expect(win.querySelector('.at-win__title')!.textContent).toBe('search');
    expect(Array.from(root.querySelectorAll('.at-cmd__group')).map((g) => g.textContent)).toEqual(['Pages', 'Actions']);
    expect(options()).toHaveLength(4);
    expect(options()[0].querySelector('svg.at-icon')).not.toBeNull();
    expect(options()[3].querySelector('.at-cmd__spacer')).not.toBeNull();
    expect(options()[3].querySelector('kbd.at-kbd')!.textContent).toBe('C');
    expect(root.querySelector('.at-cmd__search kbd.at-kbd')!.textContent).toBe('esc');
  });

  it('focuses the input when autoFocus is set', () => {
    setup();
    expect(document.activeElement).toBe(input());
  });

  it('marks the first option active and wires aria-activedescendant', () => {
    setup();
    expect(activeLabel()).toBe('Home');
    expect(options()[0].getAttribute('aria-selected')).toBe('true');
    expect(input().getAttribute('aria-activedescendant')).toBe(options()[0].id);
    expect(input().getAttribute('aria-controls')).toBe(root.querySelector('[role="listbox"]')!.id);
  });

  it('moves with ArrowDown / ArrowUp and stops at both ends', () => {
    setup();
    expect(key('ArrowDown').defaultPrevented).toBe(true);
    expect(activeLabel()).toBe('Projects');
    key('ArrowDown');
    key('ArrowDown');
    key('ArrowDown');
    expect(activeLabel()).toBe('Copy email');
    key('ArrowUp');
    expect(activeLabel()).toBe('Switch to the Sage theme');
    key('ArrowUp');
    key('ArrowUp');
    key('ArrowUp');
    expect(activeLabel()).toBe('Home');
    expect(input().getAttribute('aria-activedescendant')).toBe(options()[0].id);
  });

  it('selects the active item with Enter, passing the original item and its group', () => {
    const { onSelect } = setup();
    key('ArrowDown');
    key('Enter');
    expect(onSelect).toHaveBeenCalledWith(groups[0].items[1], 'Pages');
  });

  it('filters on input and resets the selection to the first match', () => {
    const { onSelect } = setup();
    key('ArrowDown');
    type('mode');
    expect(options().map((o) => o.querySelector('.at-cmd__label')!.textContent)).toEqual(['Switch to the Sage theme']);
    expect(activeLabel()).toBe('Switch to the Sage theme');
    expect(Array.from(root.querySelectorAll('.at-cmd__group')).map((g) => g.textContent)).toEqual(['Actions']);
    key('Enter');
    expect(onSelect).toHaveBeenCalledWith(groups[1].items[0], 'Actions');
  });

  it('shows the empty state and ignores Enter when nothing matches', () => {
    const { onSelect } = setup();
    type('zzz');
    expect(options()).toHaveLength(0);
    expect(root.querySelector('.at-cmd__empty')!.textContent).toBe('Nothing matches “zzz”');
    expect(input().hasAttribute('aria-activedescendant')).toBe(false);
    key('Enter');
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('closes on Escape', () => {
    const { onClose } = setup();
    key('Escape');
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('activates on mouse move and selects on click', () => {
    const { onSelect } = setup();
    act(() => {
      options()[2].dispatchEvent(new MouseEvent('mousemove', { bubbles: true }));
    });
    expect(activeLabel()).toBe('Switch to the Sage theme');
    act(() => {
      options()[3].click();
    });
    expect(onSelect).toHaveBeenCalledWith(groups[1].items[1], 'Actions');
  });

  it('replaces the hint of the flashed item', () => {
    setup({ flash: { item: groups[1].items[1], text: 'Copied' } });
    const hint = options()[3].querySelector('.at-cmd__hint')!;
    expect(hint.textContent).toBe('Copied');
    expect(options()[0].querySelector('.at-cmd__hint')!.textContent).toBe('/');
  });
});
