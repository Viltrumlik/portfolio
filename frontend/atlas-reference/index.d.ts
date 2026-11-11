import type * as React from 'react';

export type IconName = 'arrow-up-right' | 'arrow-right' | 'check' | 'x' | 'plus' | 'search' | 'refresh' | 'link' | 'star' | 'fork' | 'commit' | 'clock' | 'alert' | 'zap' | 'music' | 'code' | 'pin' | 'power';
export interface IconProps { name: IconName; size?: number; strokeWidth?: number; title?: string; className?: string }
export declare function Icon(props: IconProps): React.ReactElement | null;

export interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'md' | 'sm';
  icon?: IconName;
  iconRight?: IconName;
  /** Renders an <a> styled as a button. */
  href?: string;
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): React.ReactElement;

export interface KbdProps { children: React.ReactNode; className?: string }
export declare function Kbd(props: KbdProps): React.ReactElement;

export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: React.ReactNode;
  /** Replaces the hint and marks the field invalid. */
  error?: React.ReactNode;
}
export declare function TextField(props: TextFieldProps): React.ReactElement;

export interface SwitchProps { checked?: boolean; defaultChecked?: boolean; onChange?: (next: boolean) => void; label?: string; disabled?: boolean; id?: string; className?: string }
export declare function Switch(props: SwitchProps): React.ReactElement;

export interface BadgeProps { tone?: 'neutral' | 'accent' | 'live' | 'danger'; dot?: boolean; pulse?: boolean; className?: string; children?: React.ReactNode }
export declare function Badge(props: BadgeProps): React.ReactElement;

export interface ServiceCodeProps { code: string; label?: string; size?: 'sm' | 'md' | 'lg'; className?: string }
export declare function ServiceCode(props: ServiceCodeProps): React.ReactElement;

export interface WindowProps {
  /** Lowercase file name shown in the title bar: "about.md", "github.app". */
  title: string;
  /** Lime title bar. One active window per screen. */
  active?: boolean;
  /** Content at the right end of the title bar (a Kbd, a Switch). */
  barEnd?: React.ReactNode;
  label?: string;
  role?: string;
  id?: string;
  className?: string;
  bodyClassName?: string;
  style?: React.CSSProperties;
  onBarPointerDown?: (e: React.PointerEvent<HTMLDivElement>) => void;
  children?: React.ReactNode;
}
export declare function Window(props: WindowProps): React.ReactElement;

export interface DesktopItem {
  id: string;
  title: string;
  /** CSS length, usually a percentage of the desk width. */
  x: string;
  /** Pixels from the top of the desk. */
  y: number;
  /** CSS width, usually a percentage. */
  w: string;
  content: React.ReactNode;
  label?: string;
  className?: string;
}
export interface DesktopProps { items: DesktopItem[]; height?: number; activeId?: string; className?: string; children?: React.ReactNode }
export declare function Desktop(props: DesktopProps): React.ReactElement;

export interface DockItem { code: string; label: string; href?: string; onClick?: () => void; active?: boolean }
export interface DockProps { items: DockItem[]; label?: string; className?: string }
export declare function Dock(props: DockProps): React.ReactElement;

export interface SiteHeaderLink { label: string; href?: string; active?: boolean }
export interface SiteHeaderProps {
  name: string;
  links?: SiteHeaderLink[];
  status?: { label: string; pulse?: boolean };
  /** Shows "<city> HH:MM" in the owner's time zone. */
  city?: string;
  timeZone?: string;
  onCommand?: () => void;
  homeHref?: string;
}
export declare function SiteHeader(props: SiteHeaderProps): React.ReactElement;

export interface CommandItem { label: string; hint?: string; icon?: IconName; shortcut?: string; keywords?: string; [key: string]: unknown }
export interface CommandGroup { label: string; items: CommandItem[] }
export interface CommandPaletteProps {
  groups: CommandGroup[];
  onSelect?: (item: CommandItem & { group: string }) => void;
  onClose?: () => void;
  placeholder?: string;
  label?: string;
  title?: string;
  autoFocus?: boolean;
  className?: string;
}
export declare function CommandPalette(props: CommandPaletteProps): React.ReactElement;

export interface SectionHeaderProps { title: React.ReactNode; index?: string; kicker?: string; action?: React.ReactNode }
export declare function SectionHeader(props: SectionHeaderProps): React.ReactElement;

export interface ProjectRowProps {
  index: string;
  title: string;
  summary?: string;
  stack?: string[];
  /** Right-hand column: a year or a kind ("Bot"). */
  meta?: React.ReactNode;
  /** @deprecated use meta */
  year?: React.ReactNode;
  status?: { label: string; tone?: BadgeProps['tone']; dot?: boolean };
  href?: string;
}
export declare function ProjectRow(props: ProjectRowProps): React.ReactElement;

export interface StatProps { value: React.ReactNode; label: string; unit?: string; delta?: string; trend?: 'up' | 'down' }
export declare function Stat(props: StatProps): React.ReactElement;

export interface ContributionGraphProps {
  /** Daily counts, oldest first, starting on a Sunday. */
  data?: number[];
  weeks?: number;
  seed?: number;
  total?: number;
  label?: string;
  cell?: number;
  gap?: number;
}
export declare function ContributionGraph(props: ContributionGraphProps): React.ReactElement;

export interface RepoCardProps { name: string; owner?: string; description?: string; language?: string; stars?: number; forks?: number; updated?: string; href?: string; pinned?: boolean }
export declare function RepoCard(props: RepoCardProps): React.ReactElement;

export interface ActivityItem { time: string; datetime?: string; code: string; source?: string; text: React.ReactNode; meta?: string; tone?: 'danger' }
export interface ActivityFeedProps { items: ActivityItem[]; label?: string }
export declare function ActivityFeed(props: ActivityFeedProps): React.ReactElement;

export interface NowCardProps {
  timeZone?: string;
  location?: string;
  utc?: string;
  status?: { label: string; tone?: BadgeProps['tone']; pulse?: boolean };
  coding?: { project: string; detail?: string };
  listening?: { track: string; artist?: string };
  label?: string;
  title?: string;
  active?: boolean;
}
export declare function NowCard(props: NowCardProps): React.ReactElement;

export interface IntegrationCardProps {
  name: string;
  code: string;
  description?: string;
  status?: 'off' | 'syncing' | 'connected' | 'error';
  account?: string;
  lastSync?: string;
  scopes?: string[];
  error?: string;
  onConnect?: () => void;
  onSync?: () => void;
  onDisconnect?: () => void;
}
export declare function IntegrationCard(props: IntegrationCardProps): React.ReactElement;

export interface RuleStep { code: string; service?: string; label: string; detail?: string }
export interface AutomationRuleProps { trigger: RuleStep; action: RuleStep; enabled?: boolean; defaultEnabled?: boolean; onToggle?: (next: boolean) => void; runs?: number; lastRun?: string; title?: string; label?: string }
export declare function AutomationRule(props: AutomationRuleProps): React.ReactElement;

declare global {
  interface Window {
    Atlas: {
      Icon: typeof Icon; Button: typeof Button; Kbd: typeof Kbd; TextField: typeof TextField; Switch: typeof Switch;
      Badge: typeof Badge; ServiceCode: typeof ServiceCode; Window: typeof Window; Desktop: typeof Desktop; Dock: typeof Dock; SiteHeader: typeof SiteHeader; CommandPalette: typeof CommandPalette;
      SectionHeader: typeof SectionHeader; ProjectRow: typeof ProjectRow; Stat: typeof Stat; ContributionGraph: typeof ContributionGraph;
      RepoCard: typeof RepoCard; ActivityFeed: typeof ActivityFeed; NowCard: typeof NowCard; IntegrationCard: typeof IntegrationCard;
      AutomationRule: typeof AutomationRule;
    };
  }
}
