#!/usr/bin/env node
// Generates src/atlas/tokens.css from src/atlas/tokens.json.
// Run by `npm run tokens` (and automatically before `dev` and `build`).
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HEADER = '/* Generated from tokens.json by scripts/tokens-to-css.mjs. Do not edit by hand. */';

/** "{signal}" (or any "{name}" inside a value) -> "var(--signal)". */
function resolveAliases(value) {
  return String(value).replace(/\{([a-z0-9-]+)\}/gi, 'var(--$1)');
}

/** A token value for one theme: per-theme objects pick their entry, plain strings apply to every theme. */
function valueFor(value, themeId, fallbackThemeId) {
  if (value !== null && typeof value === 'object') {
    return value[themeId] ?? value[fallbackThemeId];
  }
  return value;
}

function rule(selector, declarations) {
  const body = declarations.map(([prop, val]) => `  ${prop}: ${val};`).join('\n');
  return `${selector} {\n${body}\n}`;
}

function kebab(prop) {
  return prop.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);
}

const TYPE_PROPS = ['fontSize', 'lineHeight', 'fontWeight', 'letterSpacing', 'fontStyle', 'textTransform', 'fontVariantNumeric'];

function typeClass(style, family) {
  const decls = [['font-family', `var(--font-${family})`]];
  for (const prop of TYPE_PROPS) {
    if (style[prop] != null) decls.push([kebab(prop), String(style[prop])]);
  }
  const usage = style.usage || '';
  if (style.textTransform == null && /uppercased/i.test(usage)) decls.push(['text-transform', 'uppercase']);
  if (style.fontVariantNumeric == null && /tabular/i.test(usage)) decls.push(['font-variant-numeric', 'tabular-nums']);
  return rule(`.${style.name}`, decls);
}

/**
 * @param {any} tokens parsed tokens.json
 * @returns {string} CSS text
 */
export function tokensToCss(tokens) {
  const themes = tokens.color?.themes ?? [{ id: 'dark' }];
  const defaultTheme = themes[0].id;
  const themed = [...(tokens.color?.tokens ?? []), ...(tokens.shadow?.tokens ?? [])];

  const blocks = [HEADER];

  themes.forEach((theme, i) => {
    const selector = i === 0 ? `:root,\n[data-theme="${theme.id}"]` : `[data-theme="${theme.id}"]`;
    const decls = [['color-scheme', theme.id === 'light' ? 'light' : 'dark']];
    for (const token of themed) {
      const v = valueFor(token.value, theme.id, defaultTheme);
      if (v != null) decls.push([`--${token.name}`, resolveAliases(v)]);
    }
    blocks.push(rule(selector, decls));
  });

  const rootDecls = [];
  for (const family of ['spacing', 'radius', 'layout']) {
    for (const token of tokens[family]?.tokens ?? []) {
      rootDecls.push([`--${token.name}`, resolveAliases(valueFor(token.value, defaultTheme, defaultTheme))]);
    }
  }
  for (const [name, stack] of Object.entries(tokens.type?.families ?? {})) {
    rootDecls.push([`--font-${name}`, stack]);
  }
  blocks.push(rule(':root', rootDecls));

  for (const group of tokens.type?.groups ?? []) {
    for (const style of group.styles ?? []) {
      blocks.push(typeClass(style, style.family ?? group.family ?? 'sans'));
    }
  }

  return blocks.join('\n\n') + '\n';
}

function main() {
  const src = new URL('../src/atlas/tokens.json', import.meta.url);
  const out = new URL('../src/atlas/tokens.css', import.meta.url);
  const css = tokensToCss(JSON.parse(readFileSync(src, 'utf8')));
  writeFileSync(out, css);
  console.log(`tokens.css written (${css.length} bytes) -> ${fileURLToPath(out)}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
