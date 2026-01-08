# Figma Analytics File — Usage & Export Guide

This README explains how to surface the Figma file for analytics dashboards and how to embed exported visuals in the repo.

## Location

- Primary Figma file: <link to Figma file to be added by Design team>
- Recommended repo path for exports: `figma/exports/` (store PNG/SVG, and optional JSON export for programmatic usage)

## Export recommendations

- Exports:
  - `dashboard-preview.png` — 1200x630 for README preview
  - `dashboard-panels/*.svg` — individual panels for embedding and high-fidelity export
  - `dashboard-frames.json` — (optional) Figma JSON export for automated ingestion
- Naming: `kpiname_v1.{png,svg}` with semantic suffixes (e.g., `par_90_v1.svg`)

## Embedding in Markdown

Example:

```md
![KPI dashboard preview](figma/exports/dashboard-preview.png)
```

For a live Figma embed (internal use, requires Figma access):

```html
<iframe
  width="800"
  height="450"
  src="https://www.figma.com/embed?embed_host=share&url=FIGMA_URL"
  allowfullscreen
></iframe>
```

## Permissions & Collaboration

- Ensure that the Figma file is viewable by the engineering and analytics teams.
- When major changes to KPI visuals are made, include a short changelog in `figma/CHANGELOG.md` and add a link to the PR.

## Automation ideas

- Consider a scheduled job that exports the frame PNG/SVG to `figma/exports/` and commits to a `chore/figma-exports` branch for review.
