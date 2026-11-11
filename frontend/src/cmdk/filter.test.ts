import { describe, expect, it } from 'vitest';
import { filterCommands } from './filter';
import { groups } from './fixtures';

const labels = (q: string) => filterCommands(groups, q).map((r) => r.item.label);

describe('filterCommands', () => {
  it('returns every item in group order for an empty query', () => {
    const all = filterCommands(groups, '');
    expect(all.map((r) => [r.group, r.item.label])).toEqual([
      ['Pages', 'Home'],
      ['Pages', 'Projects'],
      ['Actions', 'Switch to the Sage theme'],
      ['Actions', 'Copy email'],
    ]);
  });

  it('keeps a reference to the original item', () => {
    expect(filterCommands(groups, '')[0].item).toBe(groups[0].items[0]);
  });

  it('matches the label case-insensitively, ignoring outer spaces', () => {
    expect(labels('  PROJ ')).toEqual(['Projects']);
  });

  it('matches the hint', () => {
    expect(labels('example.com')).toEqual(['Copy email']);
  });

  it('matches keywords', () => {
    expect(labels('dark')).toEqual(['Switch to the Sage theme']);
  });

  it('returns nothing when nothing matches', () => {
    expect(labels('zzz')).toEqual([]);
  });

  it('tolerates groups without items', () => {
    expect(filterCommands([{ label: 'Empty' } as never, ...groups], 'home').length).toBe(1);
  });
});
