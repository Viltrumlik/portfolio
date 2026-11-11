import { afterEach, describe, expect, it, vi } from 'vitest';
import { formatClock, initClock } from './clock';

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('formatClock', () => {
  const date = new Date('2026-01-15T09:05:07Z'); // Tashkent is UTC+5, no DST

  it('formats HH:MM in the given zone, 24 h', () => {
    expect(formatClock(date, 'Asia/Tashkent', 'HH:MM')).toBe('14:05');
  });

  it('formats HH:MM:SS', () => {
    expect(formatClock(date, 'Asia/Tashkent', 'HH:MM:SS')).toBe('14:05:07');
  });

  it('shows midnight as 00, never 24', () => {
    expect(formatClock(new Date('2026-01-15T19:00:00Z'), 'Asia/Tashkent', 'HH:MM')).toBe('00:00');
  });

  it('pads single digits and handles other zones', () => {
    expect(formatClock(new Date('2026-07-01T08:03:09Z'), 'UTC', 'HH:MM:SS')).toBe('08:03:09');
    expect(formatClock(new Date('2026-07-01T08:03:09Z'), 'America/New_York', 'HH:MM')).toBe('04:03');
  });
});

describe('initClock', () => {
  it('renders immediately and then every second', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-15T09:05:58Z'));
    document.body.innerHTML = '<time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM:SS">--:--</time>';
    const el = document.querySelector('time')!;
    initClock(el);
    expect(el.textContent).toBe('14:05:58');
    vi.advanceTimersByTime(1000);
    expect(el.textContent).toBe('14:05:59');
    vi.advanceTimersByTime(1000);
    expect(el.textContent).toBe('14:06:00');
    expect(el.getAttribute('datetime')).toBe('2026-01-15T09:06:00.000Z');
  });

  it('defaults to HH:MM', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-15T09:05:58Z'));
    document.body.innerHTML = '<time data-island="clock" data-tz="Asia/Tashkent"></time>';
    const el = document.querySelector('time')!;
    initClock(el);
    expect(el.textContent).toBe('14:05');
  });

  it('leaves the server-rendered text alone for an unknown zone', () => {
    document.body.innerHTML = '<time data-island="clock" data-tz="Mars/Olympus">14:05</time>';
    const el = document.querySelector('time')!;
    expect(() => initClock(el)).not.toThrow();
    expect(el.textContent).toBe('14:05');
  });

  it('returns a stop function that halts updates', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-15T09:05:58Z'));
    document.body.innerHTML = '<time data-tz="UTC" data-format="HH:MM:SS"></time>';
    const el = document.querySelector('time')!;
    const stop = initClock(el);
    stop();
    vi.advanceTimersByTime(5000);
    expect(el.textContent).toBe('09:05:58');
  });
});
