import type { CommandGroup, CommandItem } from './types';

export interface CommandMatch {
  group: string;
  item: CommandItem;
}

/** Flattens groups in order, keeping items whose label + hint + keywords contain the query. */
export function filterCommands(groups: readonly CommandGroup[], query: string): CommandMatch[] {
  const needle = query.trim().toLowerCase();
  const out: CommandMatch[] = [];
  for (const g of groups) {
    for (const item of g.items ?? []) {
      const hay = `${item.label} ${item.hint ?? ''} ${item.keywords ?? ''}`.toLowerCase();
      if (!needle || hay.includes(needle)) out.push({ group: g.label, item });
    }
  }
  return out;
}
