# RepoCard

A repository as a small window without a title bar: mono name, a two-line description, language, stars, forks and when it was last updated.

**Provide:** `owner`, `name`, `description`, `language`, `stars`, `forks` and `updated` (relative). Optional: `pinned` and `href`.

- **Use it for** pinned repos pulled from GitHub. A curated case study is a `ProjectRow` instead.
- **Language** is shown as a lime dot. Don't use GitHub's language colors.
- **Layout.** Use `.at-grid`, with columns at least 280px wide.
