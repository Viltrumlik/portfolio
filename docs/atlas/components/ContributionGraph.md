# ContributionGraph

The GitHub contribution calendar drawn in the `heat-0`…`heat-4` phosphor scale, with a total and a legend. The busiest days bloom, and a few of them fade in and out.

**Provide:** `data`, an array of daily counts, oldest first, starting on a Sunday (from GitHub's `contributionCalendar` weeks). Optional: `total`, `label`, `weeks` and `seed` (sample data when `data` is absent), `cell` and `gap`.

- **Levels** are quarters of the busiest day.
- **Accessibility.** Each cell has a tooltip with its count, and the graph has an accessible label with the total.
- **Placement.** Put it in a window titled "commits.log". On phones it scrolls sideways inside its window.
