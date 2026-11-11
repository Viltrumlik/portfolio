# Badge

One or two words of status in a pill.

**Provide:** the words as `children`. Optional: `tone` (`neutral`, `live`, `accent`, `danger`), `dot` and `pulse`.

- **`live` with a static dot:** connected or available.
- **`accent` with a pulsing dot:** work in progress ("Syncing").
- **`live` and `accent`:** both use `signal` on `signal-soft`, so the word and the pulse tell them apart.
- **`danger` with the alert `Icon`:** failed or expired.
- **`neutral`:** everything else ("Draft", "Pinned").
- Pulse at most two things on screen.
