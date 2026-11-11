import type { CommandGroup } from './types';

export const groups: CommandGroup[] = [
  {
    label: 'Pages',
    items: [
      { label: 'Home', hint: '/', icon: 'arrow-right', href: '/' },
      { label: 'Projects', hint: '/projects/', icon: 'code', href: '/projects/' },
    ],
  },
  {
    label: 'Actions',
    items: [
      { label: 'Switch to the Sage theme', icon: 'zap', action: 'theme', keywords: 'light dark mode appearance' },
      { label: 'Copy email', hint: 'me@example.com', action: 'copy:me@example.com', shortcut: 'C' },
    ],
  },
];
