// @vitest-environment node
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

// phosphor-dim is 3.4–4.1:1 on a window in every theme: fine for decoration, too faint for text.
const SHEETS = ['./components.css', '../site.css'];

/** [selector, declarations] for every innermost rule in a stylesheet, comments removed. */
function rules(css: string): Array<[string, string]> {
  const out: Array<[string, string]> = [];
  for (const m of css.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    out.push([m[1].trim(), m[2]]);
  }
  return out;
}

describe('phosphor-dim', () => {
  it.each(SHEETS)('only colours decorative ::before/::after prefixes in %s', (sheet) => {
    const css = readFileSync(new URL(sheet, import.meta.url), 'utf8');
    const textSelectors = rules(css)
      .filter(([, body]) => /(^|[;\s])color:\s*var\(--phosphor-dim\)/.test(body))
      .flatMap(([selector]) => selector.split(',').map((s) => s.trim()))
      .filter((s) => !/::(before|after)$/.test(s));
    expect(textSelectors).toEqual([]);
  });
});
