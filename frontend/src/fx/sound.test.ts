import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { initSound, SOUND_KEY } from './sound';

class FakeAudio {
  static instances: FakeAudio[] = [];
  currentTime = 0;
  destination = {};
  state = 'running';
  oscillators = 0;
  constructor() {
    FakeAudio.instances.push(this);
  }
  resume() {
    return Promise.resolve();
  }
  createOscillator() {
    this.oscillators++;
    return { type: '', frequency: { setValueAtTime() {} }, connect: () => ({ connect() {} }), start() {}, stop() {} };
  }
  createGain() {
    return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} };
  }
}

let off: (() => void) | null = null;

beforeEach(() => {
  localStorage.clear();
  FakeAudio.instances = [];
  document.body.innerHTML = `
    <button data-sound-toggle aria-pressed="false"><span data-sound-label>Sound off</span></button>
    <a href="#x" id="link">link</a>
    <input id="field">`;
});

afterEach(() => {
  off?.();
  off = null;
  vi.unstubAllGlobals();
});

const toggle = () => document.querySelector<HTMLElement>('[data-sound-toggle]')!;
const label = () => document.querySelector('[data-sound-label]')!.textContent;

describe('initSound', () => {
  it('is off by default and creates no audio context', () => {
    vi.stubGlobal('AudioContext', FakeAudio);
    off = initSound(document);
    expect(toggle().getAttribute('aria-pressed')).toBe('false');
    expect(label()).toBe('Sound off');
    document.getElementById('link')!.click();
    expect(FakeAudio.instances).toHaveLength(0);
  });

  it('restores a saved preference', () => {
    localStorage.setItem(SOUND_KEY, 'on');
    off = initSound(document);
    expect(toggle().getAttribute('aria-pressed')).toBe('true');
    expect(label()).toBe('Sound on');
  });

  it('the toggle turns sound on, saves it and plays on clicks and keys', () => {
    vi.stubGlobal('AudioContext', FakeAudio);
    off = initSound(document);
    toggle().click();
    expect(localStorage.getItem(SOUND_KEY)).toBe('on');
    expect(toggle().getAttribute('aria-pressed')).toBe('true');
    expect(label()).toBe('Sound on');
    const audio = FakeAudio.instances[0];
    const before = audio.oscillators;
    document.getElementById('link')!.click();
    expect(audio.oscillators).toBeGreaterThan(before);
    const afterClick = audio.oscillators;
    document.getElementById('field')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'a', bubbles: true }));
    expect(audio.oscillators).toBeGreaterThan(afterClick);
    const afterKey = audio.oscillators;
    document.dispatchEvent(new CustomEvent('atlas:themechange', { detail: { theme: 'amber' } }));
    expect(audio.oscillators).toBeGreaterThan(afterKey);
    toggle().click();
    expect(localStorage.getItem(SOUND_KEY)).toBe('off');
    expect(label()).toBe('Sound off');
  });

  it('survives blocked storage and a missing AudioContext', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.stubGlobal('AudioContext', undefined);
    off = initSound(document);
    expect(() => toggle().click()).not.toThrow();
    expect(toggle().getAttribute('aria-pressed')).toBe('true');
    expect(() => document.getElementById('link')!.click()).not.toThrow();
  });
});
