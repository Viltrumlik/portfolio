import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { applyNow, formatPlayed, initNow, type NowPayload } from './now';

const fixture: NowPayload = {
  listening: {
    track: 'Windowlicker',
    artist: 'Aphex Twin',
    url: 'https://www.last.fm/music/Aphex+Twin/_/Windowlicker',
    now_playing: false,
    played_at: '2026-01-15T09:00:00Z',
  },
  availability: { status: 'open', label: 'Open to work' },
};

const markup = `
  <section class="at-win" data-island="now" data-src="/api/live/now.json">
    <div data-now-row="listening">
      <a data-now-field="track" href="#">Old track</a>
      <span data-now-field="artist">Old artist</span>
      <span data-now-field="played">yesterday</span>
    </div>
    <span data-now-field="availability">Busy</span>
  </section>`;

const field = (name: string) => document.querySelector<HTMLElement>(`[data-now-field="${name}"]`)!;
const row = () => document.querySelector<HTMLElement>('[data-now-row="listening"]')!;

function jsonResponse(body: unknown, ok = true) {
  return { ok, status: ok ? 200 : 500, json: () => Promise.resolve(body) } as Response;
}

beforeEach(() => {
  document.body.innerHTML = markup;
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
});

describe('formatPlayed', () => {
  const now = new Date('2026-01-15T09:30:00Z');
  it('says "now playing" while the track is playing', () => {
    expect(formatPlayed({ ...fixture.listening!, now_playing: true }, now)).toBe('now playing');
  });
  it('gives a short relative time otherwise', () => {
    expect(formatPlayed({ ...fixture.listening!, played_at: '2026-01-15T09:29:40Z' }, now)).toBe('just now');
    expect(formatPlayed(fixture.listening!, now)).toBe('30 min ago');
    expect(formatPlayed({ ...fixture.listening!, played_at: '2026-01-15T06:00:00Z' }, now)).toBe('3 h ago');
    expect(formatPlayed({ ...fixture.listening!, played_at: '2026-01-12T09:00:00Z' }, now)).toBe('3 d ago');
  });
  it('is empty when there is no usable time', () => {
    expect(formatPlayed({ ...fixture.listening!, played_at: null }, now)).toBe('');
  });
});

describe('applyNow', () => {
  it('fills the listening fields and shows the row', () => {
    row().hidden = true;
    applyNow(document.querySelector('[data-island="now"]')!, fixture, new Date('2026-01-15T09:30:00Z'));
    expect(field('track').textContent).toBe('Windowlicker');
    expect(field('artist').textContent).toBe('Aphex Twin');
    expect(field('played').textContent).toBe('30 min ago');
    expect(field('track').getAttribute('href')).toBe(fixture.listening!.url);
    expect(field('availability').textContent).toBe('Open to work');
    expect(row().hidden).toBe(false);
  });

  it('hides the listening row when listening is null', () => {
    applyNow(document.querySelector('[data-island="now"]')!, { ...fixture, listening: null });
    expect(row().hidden).toBe(true);
    expect(field('track').textContent).toBe('Old track');
  });

  it('writes text, never markup, and refuses non-http links', () => {
    applyNow(document.querySelector('[data-island="now"]')!, {
      ...fixture,
      listening: { ...fixture.listening!, track: '<img src=x onerror=alert(1)>', url: 'javascript:alert(1)' },
    });
    expect(field('track').textContent).toBe('<img src=x onerror=alert(1)>');
    expect(field('track').querySelector('img')).toBeNull();
    expect(field('track').getAttribute('href')).toBe('#');
  });
});

describe('initNow', () => {
  it('fetches once on load and then every 60 s', async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(fixture));
    vi.stubGlobal('fetch', fetchMock);
    initNow(document.querySelector('[data-island="now"]')!);
    await vi.advanceTimersByTimeAsync(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/live/now.json');
    expect(field('track').textContent).toBe('Windowlicker');

    await vi.advanceTimersByTimeAsync(59_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1_000);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('keeps the last values when the request fails or returns an error', async () => {
    vi.useFakeTimers();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(fixture))
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockResolvedValueOnce(jsonResponse({ detail: 'boom' }, false))
      .mockResolvedValueOnce(jsonResponse('not an object'));
    vi.stubGlobal('fetch', fetchMock);
    initNow(document.querySelector('[data-island="now"]')!);
    await vi.advanceTimersByTimeAsync(0);
    for (let i = 0; i < 3; i++) await vi.advanceTimersByTimeAsync(60_000);
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(field('track').textContent).toBe('Windowlicker');
    expect(row().hidden).toBe(false);
  });

  it('does nothing without data-src', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const el = document.querySelector<HTMLElement>('[data-island="now"]')!;
    el.removeAttribute('data-src');
    initNow(el);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
