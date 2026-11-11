# AutomationRule

A trigger-to-action rule, read as a sentence ("When … then …"), with run stats and an on/off switch. It is a window titled "rules/<trigger>-to-<action>".

**Provide:**
- `trigger` and `action`, each `{ code, service, label, detail }`.
- Either `enabled` with `onToggle(next)`, or `defaultEnabled`.
- Optional: `runs`, `lastRun` and `title`.

- **One trigger, one action.** For a chain, use several rules.
- **New rules** start off until the owner has seen one run.
