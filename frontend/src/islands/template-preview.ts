// Template preview island: live-renders {{key}} / {{a.b}} placeholders against a JSON sample.

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

const PLACEHOLDER = /\{\{\s*([A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*)\s*\}\}/g;

function lookup(sample: unknown, path: string): string {
  let cur: unknown = sample;
  for (const key of path.split('.')) {
    if (cur === null || typeof cur !== 'object' || !Object.prototype.hasOwnProperty.call(cur, key)) return '';
    cur = (cur as Record<string, unknown>)[key];
  }
  return typeof cur === 'string' || typeof cur === 'number' || typeof cur === 'boolean' ? String(cur) : '';
}

/** Plain text in, plain text out: callers must assign the result with textContent. */
export function renderTemplate(template: string, sample: unknown): string {
  return template.replace(PLACEHOLDER, (_, path: string) => lookup(sample, path));
}

function parseSample(raw: string | undefined): Json {
  try {
    return raw ? (JSON.parse(raw) as Json) : {};
  } catch {
    return {};
  }
}

export function initTemplatePreview(root: HTMLElement): () => void {
  const input = root.querySelector<HTMLTextAreaElement | HTMLInputElement>('[data-template-input]');
  const output = root.querySelector<HTMLElement>('[data-template-output]');
  if (!input || !output) return () => {};
  const sample = parseSample(root.dataset.sample);
  const render = () => {
    output.textContent = renderTemplate(input.value, sample);
  };
  render();
  input.addEventListener('input', render);
  return () => input.removeEventListener('input', render);
}
