// @vitest-environment node
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

// The rain canvas repaints the whole screen ~20 times a second. Anything that must be recomputed
// on every one of those frames (a backdrop blur over it, a filter on an endless animation) makes
// the page stutter on ordinary laptops.
const SHEETS = ['./components.css', '../site.css', '../islands.css', '../studio.css', '../fx/fx.css'];
const css = (sheet: string) => readFileSync(new URL(sheet, import.meta.url), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');

describe('performance guards', () => {
  it.each(SHEETS)('%s has no backdrop-filter', (sheet) => {
    expect(css(sheet)).not.toMatch(/backdrop-filter\s*:/);
  });

  it('graph cells neither animate forever nor carry a filter', () => {
    const rules = [...css('./components.css').matchAll(/([^{}]+)\{([^{}]*)\}/g)]
      .filter(([, selector]) => selector.includes('.at-graph__cell'))
      .map(([, , body]) => body);
    expect(rules.length).toBeGreaterThan(0);
    for (const body of rules) expect(body).not.toMatch(/\b(animation|filter)\s*:/);
  });
});
