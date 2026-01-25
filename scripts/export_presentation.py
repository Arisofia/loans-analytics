"""
Generate presentation-ready artifacts (HTML + Markdown) using the ABACO theme.
These exports mirror the Streamlit dashboard so you can re-create the "dark slides"
and the supplied Figma visual. Run this script from the repo root; it writes into
exports/presentation/.
"""

import textwrap
from pathlib import Path

import pandas as pd
import plotly.express as px

from src.analytics import project_growth
from src.theme import ABACO_THEME


def apply_theme(fig: px.Figure) -> px.Figure:
    fig.update_layout(
        template="plotly_dark",
        font_family=ABACO_THEME["typography"]["primary_font"],
        font_color=ABACO_THEME["colors"]["white"],
        paper_bgcolor=ABACO_THEME["colors"]["background"],
        plot_bgcolor=ABACO_THEME["colors"]["background"],
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
    )
    return fig


def build_growth_chart(output_dir: Path) -> Path:
    projection = project_growth(
        yield_start=1.2,
        yield_end=2.1,
        volume_start=120,
        volume_end=205,
        periods=6,
    )
    projection["month_label"] = projection["date"].dt.strftime("%b %Y")
    fig = px.line(
        projection,
        x="month_label",
        y=["yield", "loan_volume"],
        markers=True,
        title="Projected Growth Path",
    )
    apply_theme(fig)
    output_path = output_dir / "growth-path.html"
    fig.write_html(
        str(output_path),
        include_plotlyjs="cdn",
        full_html=False,
    )
    return output_path


def build_treemap(output_dir: Path) -> Path:
    treemap_data = pd.DataFrame(
        {
            "segment": ["Primary", "Secondary", "Retail", "SMB", "Wholesale"],
            "principal_balance": [510, 420, 360, 280, 160],
        }
    )
    fig = px.treemap(
        treemap_data,
        path=["segment"],
        values="principal_balance",
        title="Marketing & Sales Treemap",
    )
    apply_theme(fig)
    output_path = output_dir / "sales-treemap.html"
    fig.write_html(
        str(output_path),
        include_plotlyjs="cdn",
        full_html=False,
    )
    return output_path


def build_markdown_summary(output_dir: Path) -> Path:
    summary = textwrap.dedent(
        """
        # ABACO Slide Assets

        - **Theme:** Dark gradients with neon purple/blue accents to mirror the Figma “Dark Editable Slides”.
        - **Growth path:** See the interactive chart exported as `growth-path.html`.
        - **Marketing treemap:** Use `sales-treemap.html` to explain segment weighting.
        - **Financeable offers:** Emphasize that the pipeline highlights financeable borrowers and packages, not just raw demand.
        - **Data source:** Import the CSV produced by `streamlit_app.py` (download fact table from the app).
        - **Compliance & auditability:** Call out the AI guardrails and decision traceability supporting regulatory readiness.
        - **Narrative:** Focus on delinquency control, yield expansion, and operational automation.

        Use the HTML files as iframe backgrounds or screenshot them for Figma. Keep the markdown text for slide captions, KPIs, and spotlight highlights.
        """
    ).strip()
    summary_path = output_dir / "presentation-summary.md"
    summary_path.write_text(summary)
    return summary_path


def main():
    output_dir = Path("exports/presentation")
    output_dir.mkdir(parents=True, exist_ok=True)
    growth_chart = build_growth_chart(output_dir)
    treemap = build_treemap(output_dir)
    summary = build_markdown_summary(output_dir)
    print("Exports ready:")
    print(f"- Growth chart: {growth_chart}")
    print(f"- Treemap: {treemap}")
    print(f"- Summary: {summary}")


if __name__ == "__main__":
    main()
