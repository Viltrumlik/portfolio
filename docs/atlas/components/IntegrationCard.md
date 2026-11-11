# IntegrationCard

One connected service, shown as a window titled "connections/<name>". It shows the service's code and what it feeds, its state, facts about the connection, and the next action.

**Provide:**
- `name`, `code` and `description`.
- `status`: `off`, `syncing`, `connected` or `error`.
- When connected: `account`, `lastSync` and `scopes`.
- In the error state: the `error` text.
- Handlers: `onConnect`, `onSync` and `onDisconnect`.

- **Error state.** The outline turns `danger`, and so does the title bar, on `danger-soft`.
- **Primary action.** Exactly one per state: Connect, Reconnect, or none.
- **Secrets.** Show only handles and masked keys (`API key •••• 91ab`).
- **Copy.** See the "Connections and automation" section for each state's wording.
