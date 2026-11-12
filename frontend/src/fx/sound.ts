// Sound: off by default. [data-sound-toggle] buttons flip it (aria-pressed + [data-sound-label]).
// When on, tiny WebAudio-synthesised clicks, keystroke ticks and a theme blip — no audio files.

export const SOUND_KEY = 'atlas:sound';

type AudioCtor = typeof AudioContext;

function readPref(win: Window): boolean {
  try {
    return win.localStorage.getItem(SOUND_KEY) === 'on';
  } catch {
    return false;
  }
}

function writePref(win: Window, on: boolean): void {
  try {
    win.localStorage.setItem(SOUND_KEY, on ? 'on' : 'off');
  } catch {
    /* storage blocked: the choice lasts for this page only */
  }
}

export function initSound(doc: Document = document): () => void {
  const win = doc.defaultView ?? window;
  let on = readPref(win);
  let audio: AudioContext | null = null;

  const sync = () => {
    doc.querySelectorAll('[data-sound-toggle]').forEach((t) => t.setAttribute('aria-pressed', String(on)));
    doc.querySelectorAll('[data-sound-label]').forEach((l) => (l.textContent = on ? 'Sound on' : 'Sound off'));
  };

  /** Created lazily, from inside a user gesture, so browsers allow it to play. */
  const context = (): AudioContext | null => {
    if (audio) return audio;
    const w = win as Window & { AudioContext?: AudioCtor; webkitAudioContext?: AudioCtor };
    const Ctor = w.AudioContext ?? w.webkitAudioContext;
    if (typeof Ctor !== 'function') return null;
    try {
      audio = new Ctor();
    } catch {
      return null;
    }
    return audio;
  };

  const tone = (freq: number, ms: number, type: OscillatorType, peak: number, delay = 0) => {
    const ctx = audio;
    if (!ctx) return;
    try {
      if (ctx.state === 'suspended') void ctx.resume();
      const t = ctx.currentTime + delay;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(peak, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + ms / 1000);
      osc.connect(gain).connect(ctx.destination);
      osc.start(t);
      osc.stop(t + ms / 1000 + 0.02);
    } catch {
      /* audio graph unavailable: stay silent */
    }
  };

  const click = () => tone(1800, 14, 'square', 0.035);
  const tick = () => tone(900 + Math.random() * 500, 10, 'triangle', 0.025);
  const blip = () => {
    tone(660, 60, 'sine', 0.05);
    tone(990, 70, 'sine', 0.05, 0.07);
  };

  const onClick = (e: Event) => {
    const target = e.target as Element | null;
    if (target?.closest?.('[data-sound-toggle]')) {
      on = !on;
      writePref(win, on);
      sync();
      if (on && context()) blip();
      return;
    }
    if (on && target?.closest?.('a, button') && context()) click();
  };
  const onKey = (e: Event) => {
    const target = e.target as Element | null;
    if (on && target?.closest?.('input, textarea') && context()) tick();
  };
  const onTheme = () => {
    if (on) blip();
  };

  sync();
  doc.addEventListener('click', onClick);
  doc.addEventListener('keydown', onKey);
  doc.addEventListener('atlas:themechange', onTheme);
  return () => {
    doc.removeEventListener('click', onClick);
    doc.removeEventListener('keydown', onKey);
    doc.removeEventListener('atlas:themechange', onTheme);
  };
}
