// Now island: polls a JSON endpoint and refreshes the listening row and availability label.

export interface Listening {
  track: string;
  artist?: string | null;
  url?: string | null;
  now_playing?: boolean;
  played_at?: string | null;
}
export interface NowPayload {
  listening: Listening | null;
  availability?: { status: string; label: string } | null;
}

export const POLL_MS = 60_000;

export function formatPlayed(listening: Listening, now: Date = new Date()): string {
  if (listening.now_playing) return 'now playing';
  const at = listening.played_at ? Date.parse(listening.played_at) : NaN;
  if (Number.isNaN(at)) return '';
  const minutes = Math.floor(Math.max(0, now.getTime() - at) / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.floor(hours / 24)} d ago`;
}

function setText(root: HTMLElement, name: string, value: string | null | undefined) {
  const el = root.querySelector<HTMLElement>(`[data-now-field="${name}"]`);
  if (el && value != null && el.textContent !== value) el.textContent = value;
  return el;
}

export function applyNow(root: HTMLElement, data: NowPayload, now: Date = new Date()): void {
  const row = root.querySelector<HTMLElement>('[data-now-row="listening"]');
  const listening = data.listening;
  if (row) row.hidden = !listening;
  if (listening) {
    const track = setText(root, 'track', listening.track);
    setText(root, 'artist', listening.artist ?? '');
    setText(root, 'played', formatPlayed(listening, now));
    if (track instanceof HTMLAnchorElement && listening.url && /^https?:\/\//i.test(listening.url)) {
      track.href = listening.url;
    }
  }
  if (data.availability?.label) setText(root, 'availability', data.availability.label);
}

function isPayload(x: unknown): x is NowPayload {
  if (!x || typeof x !== 'object' || !('listening' in x)) return false;
  const l = (x as NowPayload).listening;
  return l === null || (typeof l === 'object' && typeof l.track === 'string');
}

export function initNow(root: HTMLElement): () => void {
  const src = root.dataset.src;
  if (!src) return () => {};
  let stopped = false;
  const poll = async () => {
    try {
      const res = await fetch(src, { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
      if (!res.ok) return;
      const data: unknown = await res.json();
      if (!stopped && isPayload(data)) applyNow(root, data);
    } catch {
      /* offline or bad JSON: keep the last values */
    }
  };
  void poll();
  const id = setInterval(poll, POLL_MS);
  return () => {
    stopped = true;
    clearInterval(id);
  };
}
