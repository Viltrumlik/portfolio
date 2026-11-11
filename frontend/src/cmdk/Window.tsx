import type { ComponentChildren, JSX } from 'preact';

export interface WindowProps {
  title: string;
  active?: boolean;
  barEnd?: ComponentChildren;
  label?: string;
  role?: JSX.AriaRole;
  modal?: boolean;
  className?: string;
  bodyClassName?: string;
  children?: ComponentChildren;
}

/** Atlas Window: a <section> with a title bar (three controls + mono file name) over a padded body. */
export function Window({ title, active, barEnd, label, role, modal, className, bodyClassName, children }: WindowProps) {
  const cls = ['at-win', active && 'is-active', className].filter(Boolean).join(' ');
  return (
    <section class={cls} role={role} aria-label={label || title} aria-modal={modal ? 'true' : undefined}>
      <div class="at-win__bar">
        <span class="at-win__ctl" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span class="at-win__title">{title}</span>
        {barEnd ? <span class="at-win__end">{barEnd}</span> : null}
      </div>
      <div class={bodyClassName ? `at-win__body ${bodyClassName}` : 'at-win__body'}>{children}</div>
    </section>
  );
}
