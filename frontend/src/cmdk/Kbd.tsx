import type { ComponentChildren } from 'preact';

export function Kbd({ children, className }: { children: ComponentChildren; className?: string }) {
  return <kbd class={className ? `at-kbd ${className}` : 'at-kbd'}>{children}</kbd>;
}
