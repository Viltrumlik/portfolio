// @vitest-environment node
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { tokensToCss } from './tokens-to-css.mjs';

const fixture = {
  color: {
    themes: [
      { id: 'dark', name: 'Pulse' },
      { id: 'light', name: 'Sage' },
    ],
    tokens: [
      { name: 'desk', value: { dark: '#000000', light: '#ffffff' }, usage: '' },
      { name: 'signal', value: { dark: '#c5f82a', light: '#4d6a00' }, usage: '' },
      { name: 'link', value: '{signal}', usage: 'An alias of signal.' },
    ],
  },
  shadow: {
    tokens: [{ name: 'shadow-hard', value: { dark: '5px 5px 0 0 #000', light: '5px 5px 0 0 #151515' } }],
  },
  spacing: { tokens: [{ name: 'space-1', value: '4px' }] },
  radius: { tokens: [{ name: 'radius-sm', value: '8px' }] },
  layout: { tokens: [{ name: 'columns', value: '12' }] },
  type: {
    families: { sans: '"Bricolage Grotesque", sans-serif', mono: '"Martian Mono", monospace' },
    groups: [
      {
        name: 'Display',
        family: 'sans',
        styles: [
          { name: 'display-xl', fontSize: '72px', lineHeight: '72px', fontWeight: 700, letterSpacing: '-0.04em' },
        ],
      },
      {
        name: 'Data',
        family: 'mono',
        styles: [
          { name: 'mono-caps', fontSize: '10px', lineHeight: '14px', fontWeight: 500, usage: 'Uppercased by CSS.' },
          { name: 'numeral', fontSize: '28px', lineHeight: '32px', fontWeight: 500, usage: 'Tabular figures.' },
        ],
      },
    ],
  },
};

/** Body of the first rule whose selector list is exactly `selector`. */
function block(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/,\s*/g, ',\\s*');
  const match = new RegExp(`(?:^|\\n)${escaped}\\s*\\{([^}]*)\\}`).exec(css);
  if (!match) throw new Error(`no rule for ${selector}`);
  return match[1];
}

describe('tokensToCss', () => {
  const css = tokensToCss(fixture);

  it('puts the first (dark) theme on :root and [data-theme="dark"]', () => {
    const dark = block(css, ':root, [data-theme="dark"]');
    expect(dark).toContain('--desk: #000000;');
    expect(dark).toContain('--signal: #c5f82a;');
    expect(dark).toContain('--shadow-hard: 5px 5px 0 0 #000;');
    expect(dark).toContain('color-scheme: dark;');
  });

  it('emits the light theme values under [data-theme="light"]', () => {
    const light = block(css, '[data-theme="light"]');
    expect(light).toContain('--desk: #ffffff;');
    expect(light).toContain('--signal: #4d6a00;');
    expect(light).toContain('--shadow-hard: 5px 5px 0 0 #151515;');
    expect(light).toContain('color-scheme: light;');
    expect(light).not.toContain('#000000');
  });

  it('turns "{name}" aliases into var(--name) in every theme block', () => {
    expect(block(css, ':root, [data-theme="dark"]')).toContain('--link: var(--signal);');
    expect(block(css, '[data-theme="light"]')).toContain('--link: var(--signal);');
    expect(css).not.toMatch(/\{signal\}/);
  });

  it('emits theme-independent spacing, radius, layout and font family vars on :root', () => {
    const root = block(css, ':root');
    expect(root).toContain('--space-1: 4px;');
    expect(root).toContain('--radius-sm: 8px;');
    expect(root).toContain('--columns: 12;');
    expect(root).toContain('--font-sans: "Bricolage Grotesque", sans-serif;');
    expect(root).toContain('--font-mono: "Martian Mono", monospace;');
  });

  it('emits a class per type style', () => {
    const xl = block(css, '.display-xl');
    expect(xl).toContain('font-family: var(--font-sans);');
    expect(xl).toContain('font-size: 72px;');
    expect(xl).toContain('line-height: 72px;');
    expect(xl).toContain('font-weight: 700;');
    expect(xl).toContain('letter-spacing: -0.04em;');
    expect(block(css, '.mono-caps')).toContain('font-family: var(--font-mono);');
  });

  it('applies the uppercase and tabular-figure notes from the usage text', () => {
    expect(block(css, '.mono-caps')).toContain('text-transform: uppercase;');
    expect(block(css, '.numeral')).toContain('font-variant-numeric: tabular-nums;');
    expect(block(css, '.display-xl')).not.toContain('text-transform');
  });

  it('converts the real tokens.json without leftover aliases', () => {
    const real = JSON.parse(readFileSync(new URL('../src/atlas/tokens.json', import.meta.url), 'utf8'));
    const out = tokensToCss(real);
    expect(block(out, ':root, [data-theme="dark"]')).toContain('--desk: #0c0d0f;');
    expect(block(out, '[data-theme="light"]')).toContain('--desk: #b7c6ad;');
    expect(out).toContain('--link: var(--signal);');
    expect(out).toContain('--focus-ring: 0 0 0 2px #0c0d0f, 0 0 0 4px #c5f82a;');
    expect(out).toContain('.body-sm {');
    expect(out).not.toMatch(/\{[a-z-]+\}/);
  });
});
