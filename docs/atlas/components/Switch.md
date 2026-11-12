# Switch

An on/off toggle (`role="switch"`) for settings that take effect immediately. When on, the square track fills with `lime` and blooms, and the thumb springs across.

**Provide:** a `label`, plus either `checked` with `onChange(next)` or `defaultChecked`. Optional: `disabled`.

- Use it for automation rules and sync options. If a change needs a Save step, use a checkbox in a form instead.
- The label names the thing that is on ("Sync on push"), not the action ("Enable sync").
