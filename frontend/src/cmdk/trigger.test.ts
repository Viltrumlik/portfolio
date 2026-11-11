import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { initCommandPalette } from './trigger';

function setupDom(withData = true) {
  document.body.innerHTML = `
    <a href="/search/" id="open" data-cmdk-open><span id="inner">Search</span></a>
    <button id="other">Other</button>
    ${withData ? '<script type="application/json" id="atlas-cmdk">{"groups":[]}</script>' : ''}`;
}

function keydown(init: KeyboardEventInit) {
  const ev = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init });
  document.body.dispatchEvent(ev);
  return ev;
}

const flush = () => new Promise((r) => setTimeout(r, 0));

let stop: () => void = () => {};
let openPalette: ReturnType<typeof vi.fn>;
let load: ReturnType<typeof vi.fn>;

beforeEach(() => {
  openPalette = vi.fn();
  load = vi.fn().mockResolvedValue({ openPalette });
});

afterEach(() => {
  stop();
  document.body.innerHTML = '';
});

describe('initCommandPalette', () => {
  it('opens on Ctrl+K and ⌘K, lazily loading the palette once', async () => {
    setupDom();
    stop = initCommandPalette(document, load);
    expect(load).not.toHaveBeenCalled();

    expect(keydown({ key: 'k', ctrlKey: true }).defaultPrevented).toBe(true);
    await flush();
    expect(keydown({ key: 'K', metaKey: true }).defaultPrevented).toBe(true);
    await flush();

    expect(load).toHaveBeenCalledTimes(1);
    expect(openPalette).toHaveBeenCalledTimes(2);
    expect(openPalette.mock.calls[0][0]).toHaveProperty('toggleTheme');
  });

  it('ignores K without a modifier, and other modified keys', async () => {
    setupDom();
    stop = initCommandPalette(document, load);
    expect(keydown({ key: 'k' }).defaultPrevented).toBe(false);
    expect(keydown({ key: 'j', ctrlKey: true }).defaultPrevented).toBe(false);
    expect(keydown({ key: 'k', ctrlKey: true, altKey: true }).defaultPrevented).toBe(false);
    await flush();
    expect(load).not.toHaveBeenCalled();
  });

  it('opens on a click anywhere inside [data-cmdk-open], without following its link', async () => {
    setupDom();
    stop = initCommandPalette(document, load);
    const ev = new MouseEvent('click', { bubbles: true, cancelable: true });
    document.getElementById('inner')!.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(true);
    await flush();
    expect(openPalette).toHaveBeenCalledTimes(1);
    document.getElementById('other')!.click();
    await flush();
    expect(openPalette).toHaveBeenCalledTimes(1);
  });

  it('stays out of the way when the page has no #atlas-cmdk data', async () => {
    setupDom(false);
    stop = initCommandPalette(document, load);
    expect(keydown({ key: 'k', ctrlKey: true }).defaultPrevented).toBe(false);
    await flush();
    expect(load).not.toHaveBeenCalled();
  });

  it('retries the import after a failed chunk load', async () => {
    setupDom();
    load.mockRejectedValueOnce(new Error('chunk 404'));
    stop = initCommandPalette(document, load);
    keydown({ key: 'k', ctrlKey: true });
    await flush();
    expect(openPalette).not.toHaveBeenCalled();
    keydown({ key: 'k', ctrlKey: true });
    await flush();
    expect(load).toHaveBeenCalledTimes(2);
    expect(openPalette).toHaveBeenCalledTimes(1);
  });
});
