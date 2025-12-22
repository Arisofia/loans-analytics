# Presentation Export Assets
This repository now includes a `scripts/export_presentation.py` utility that renders two Plotly artifacts (growth path, marketing treemap) plus a Markdown summary that mirrors the Figma “Dark Editable Slides.” All exports land under `exports/presentation/` and reuse the ABACO theme so you can drop them directly into your slides or copy the narrative.
## How to run
```bash
pip install -r requirements.txt  # if pandas/plotly are not installed
python scripts/export_presentation.py
```
The script produces:
- `exports/presentation/growth-path.html`
- `exports/presentation/sales-treemap.html`
- `exports/presentation/presentation-summary.md`
Open the HTML files in a browser (or embed them into Figma) and use the Markdown summary for captions, KPI bullets, and Copilot prompts explaining the story.
## Operational notes
- Pair these exports with the real dataset download from `streamlit_app.py` so the slides always map to up-to-date metrics.
- You can add the script to GitHub Actions or a Copilot workflow to regenerate every time data changes before deployment.
- Run `scripts/export_copilot_slide_payload.py` to emit a JSON payload Copilot or another agent can ingest; it captures the ABACO colors/fonts plus structured slide copy so automation can reuse the same tokens for new decks.
