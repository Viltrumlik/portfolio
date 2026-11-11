import type { IconName } from './Icon';

export type { IconName };

export interface CommandItem {
  label: string;
  hint?: string;
  icon?: IconName;
  shortcut?: string;
  keywords?: string;
  /** Navigate here when chosen. */
  href?: string;
  /** "theme" flips the theme; "copy:<text>" copies <text>. */
  action?: string;
}

export interface CommandGroup {
  label: string;
  items: CommandItem[];
}

/** Shape of <script type="application/json" id="atlas-cmdk">. */
export interface CommandData {
  groups: CommandGroup[];
}
