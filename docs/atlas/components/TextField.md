# TextField

A labeled single-line input with an optional hint or error underneath. Use it inside a window.

**Provide:** a `label` plus any `<input>` props (`type`, `placeholder`, `value` with `onChange` or `defaultValue`, `name`). Optional: a `hint`, or an `error`, which replaces the hint, turns the border `danger` and adds the alert glyph.

- **Labels** are nouns ("Webhook secret").
- **Hints** say why or where ("Used to verify X-Hub-Signature-256 on every delivery.").
- **Errors** say what's wrong and how to fix it, in one sentence.
- **Secrets** use `type: 'password'`. After saving, show only the last four characters.
