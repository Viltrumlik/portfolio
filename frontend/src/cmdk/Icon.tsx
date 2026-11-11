/* Atlas glyphs: 24px grid, 1.5 stroke, round caps. Strings are paths; {c:[cx,cy,r]} circles; {p:'…'} polygons. */
type Glyph = string | { c: [number, number, number] } | { p: string };

export const ICONS = {
  'arrow-up-right': ['M7 17 17 7', 'M8 7h9v9'],
  'arrow-right': ['M4 12h15', 'M13 6l6 6-6 6'],
  check: ['M5 12.5l4.5 4.5L19 7.5'],
  x: ['M6 6l12 12', 'M18 6 6 18'],
  plus: ['M12 5v14', 'M5 12h14'],
  search: [{ c: [10.5, 10.5, 6.5] }, 'M15.5 15.5 20.5 20.5'],
  refresh: ['M20 12a8 8 0 1 1-8-8c2.2 0 4.2.9 5.65 2.35L20 8.5', 'M20 4v4.5h-4.5'],
  link: ['M9.5 14.5l5-5', 'M11 6.5l1.5-1.5a4.24 4.24 0 0 1 6 6L17 12.5', 'M13 17.5 11.5 19a4.24 4.24 0 0 1-6-6L7 11.5'],
  star: [{ p: '12 3.5 14.6 9 20.5 9.6 16 13.6 17.3 19.5 12 16.5 6.7 19.5 8 13.6 3.5 9.6 9.4 9' }],
  fork: [{ c: [6, 5, 2] }, { c: [18, 5, 2] }, { c: [12, 19, 2] }, 'M6 7v1.5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V7', 'M12 11.5V17'],
  commit: [{ c: [12, 12, 3.5] }, 'M3 12h5.5', 'M15.5 12H21'],
  clock: [{ c: [12, 12, 8.5] }, 'M12 7.5V12l3 2'],
  alert: [{ c: [12, 12, 8.5] }, 'M12 7.5v5', 'M12 16.25v.5'],
  zap: ['M13 3 5 13.5h6.5L10.5 21 19 10.5h-6.5L13 3z'],
  music: ['M9 18V6l10-2v12', { c: [6.5, 18, 2.5] }, { c: [16.5, 16, 2.5] }],
  code: ['M8.5 7 3.5 12l5 5', 'M15.5 7l5 5-5 5'],
  pin: ['M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z', { c: [12, 10, 2.25] }],
  power: ['M12 3.5v8', 'M6.5 6.5a7.5 7.5 0 1 0 11 0'],
} satisfies Record<string, Glyph[]>;

export type IconName = keyof typeof ICONS;

export interface IconProps {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  title?: string;
  className?: string;
}

export function Icon({ name, size = 16, strokeWidth = 1.5, title, className }: IconProps) {
  const def = (ICONS as Record<string, Glyph[]>)[name];
  if (!def) return null;
  return (
    <svg
      class={className ? `at-icon ${className}` : 'at-icon'}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width={strokeWidth}
      stroke-linecap="round"
      stroke-linejoin="round"
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : 'true'}
      aria-label={title}
    >
      {def.map((d, i) =>
        typeof d === 'string' ? (
          <path key={i} d={d} />
        ) : 'c' in d ? (
          <circle key={i} cx={d.c[0]} cy={d.c[1]} r={d.c[2]} />
        ) : (
          <polygon key={i} points={d.p} />
        ),
      )}
    </svg>
  );
}
