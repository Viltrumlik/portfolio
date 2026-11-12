# ProjectRow

One line of `ls -la` for a project: an index, a bold mono title, a one-line summary, the stack, and a right-hand meta column.

**Provide:**
- `index`, `title` and `summary`.
- `stack`: an array of names.
- `meta`: a year or a kind, such as "Bot".
- Optional: `status` (`{ label, tone, dot }`) and `href`.

- **Layout.** Stack the rows inside a window titled like a folder ("projects — 4 items").
- **Summary.** One sentence about what the project does for whom, not the tech.
- **Links.** With `href`, the row tints to `signal-soft` on hover, `> ` appears before the index, the title glows in `signal` and the arrow springs.
