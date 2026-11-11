// Clock island: <time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM|HH:MM:SS">.

export type ClockFormat = 'HH:MM' | 'HH:MM:SS';

const formatters = new Map<string, Intl.DateTimeFormat>();

function formatter(timeZone: string, seconds: boolean): Intl.DateTimeFormat {
  const key = `${timeZone}|${seconds}`;
  let f = formatters.get(key);
  if (!f) {
    f = new Intl.DateTimeFormat('en-GB', {
      timeZone,
      hour: '2-digit',
      minute: '2-digit',
      second: seconds ? '2-digit' : undefined,
      hourCycle: 'h23',
    });
    formatters.set(key, f);
  }
  return f;
}

/** 24-hour wall-clock time in `timeZone`. Throws RangeError for an unknown zone. */
export function formatClock(date: Date, timeZone: string, format: ClockFormat = 'HH:MM'): string {
  const seconds = format === 'HH:MM:SS';
  const parts = formatter(timeZone, seconds).formatToParts(date);
  const get = (type: Intl.DateTimeFormatPartTypes) => (parts.find((p) => p.type === type)?.value ?? '00').padStart(2, '0');
  const hh = get('hour') === '24' ? '00' : get('hour');
  return seconds ? `${hh}:${get('minute')}:${get('second')}` : `${hh}:${get('minute')}`;
}

export function initClock(el: HTMLElement): () => void {
  const timeZone = el.dataset.tz || 'UTC';
  const format: ClockFormat = el.dataset.format === 'HH:MM:SS' ? 'HH:MM:SS' : 'HH:MM';
  try {
    formatClock(new Date(), timeZone, format);
  } catch {
    return () => {}; // unknown zone: keep the server-rendered text
  }
  const tick = () => {
    const now = new Date();
    const text = formatClock(now, timeZone, format);
    if (el.textContent !== text) el.textContent = text;
    if (el instanceof HTMLTimeElement) el.dateTime = now.toISOString();
  };
  tick();
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}
