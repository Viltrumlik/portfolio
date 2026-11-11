import type { JSX } from 'preact';
import { useEffect, useId, useMemo, useRef, useState } from 'preact/hooks';
import { filterCommands } from './filter';
import { Icon } from './Icon';
import { Kbd } from './Kbd';
import type { CommandGroup, CommandItem } from './types';
import { Window } from './Window';

export interface CommandPaletteProps {
  groups: CommandGroup[];
  onSelect?: (item: CommandItem, group: string) => void;
  onClose?: () => void;
  placeholder?: string;
  label?: string;
  title?: string;
  autoFocus?: boolean;
  modal?: boolean;
  className?: string;
  /** Temporarily replaces one item's hint (e.g. "Copied"). */
  flash?: { item: CommandItem; text: string } | null;
  inputRef?: { current: HTMLInputElement | null };
}

/** Port of the Atlas CommandPalette: ↑/↓ move, ↵ chooses, esc closes; filters on label + hint + keywords. */
export function CommandPalette(props: CommandPaletteProps) {
  const { groups, onSelect, onClose, flash } = props;
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const listId = useId();
  const ownInput = useRef<HTMLInputElement>(null);
  const inputRef = props.inputRef ?? ownInput;
  const matches = useMemo(() => filterCommands(groups, query), [groups, query]);
  const optionId = (i: number) => `${listId}-o${i}`;

  useEffect(() => {
    if (props.autoFocus) inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const el = inputRef.current?.ownerDocument.getElementById(optionId(active));
    el?.scrollIntoView?.({ block: 'nearest' });
  }, [active, matches]);

  const choose = (i: number) => {
    const m = matches[i];
    if (m && onSelect) onSelect(m.item, m.group);
  };

  const onKeyDown = (e: JSX.TargetedKeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.max(0, Math.min(matches.length - 1, a + 1)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (e.key === 'Enter' && matches[active]) {
      e.preventDefault();
      choose(active);
    } else if (e.key === 'Escape' && onClose) {
      e.preventDefault();
      onClose();
    }
  };

  const rows: JSX.Element[] = [];
  let lastGroup: string | null = null;
  matches.forEach(({ group, item }, i) => {
    if (group !== lastGroup) {
      rows.push(
        <li key={`g${i}`} class="at-cmd__group" role="presentation">
          {group}
        </li>,
      );
      lastGroup = group;
    }
    const hint = flash && flash.item === item ? flash.text : item.hint;
    rows.push(
      <li
        key={i}
        id={optionId(i)}
        role="option"
        aria-selected={i === active ? 'true' : 'false'}
        class={i === active ? 'at-cmd__item is-active' : 'at-cmd__item'}
        onMouseMove={() => {
          if (active !== i) setActive(i);
        }}
        onClick={() => choose(i)}
      >
        {item.icon ? <Icon name={item.icon} size={16} /> : <span class="at-cmd__spacer" aria-hidden="true" />}
        <span class="at-cmd__label">{item.label}</span>
        {hint ? <span class="at-cmd__hint">{hint}</span> : null}
        {item.shortcut ? <Kbd>{item.shortcut}</Kbd> : null}
      </li>,
    );
  });

  return (
    <Window
      className={props.className ? `at-cmd ${props.className}` : 'at-cmd'}
      role="dialog"
      modal={props.modal}
      label={props.label || 'Command palette'}
      title={props.title || 'search'}
      active
    >
      <div class="at-cmd__search">
        <Icon name="search" size={18} />
        <input
          ref={inputRef}
          class="at-cmd__input"
          type="text"
          value={query}
          placeholder={props.placeholder || 'Search pages, projects, actions…'}
          autocomplete="off"
          spellcheck={false}
          onInput={(e) => {
            setQuery(e.currentTarget.value);
            setActive(0);
          }}
          onKeyDown={onKeyDown}
          role="combobox"
          aria-label={props.label || 'Command palette'}
          aria-expanded="true"
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={matches[active] ? optionId(active) : undefined}
        />
        <Kbd>esc</Kbd>
      </div>
      <ul id={listId} role="listbox" class="at-cmd__list">
        {rows.length ? (
          rows
        ) : (
          <li class="at-cmd__empty" role="presentation">
            {`Nothing matches “${query}”`}
          </li>
        )}
      </ul>
    </Window>
  );
}
