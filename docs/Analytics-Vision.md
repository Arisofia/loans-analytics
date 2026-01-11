# Analytics Vision & Streamlit Blueprint

## Vision statements

- **“Set the standard for financial analytics by transforming raw lending data into superior, predictive intelligence — integrating deep learning, behavioral modeling, and KPI automation into one cohesive system that powers strategic decisions at every level, all in English.”**
- **“To engineer a next-generation financial intelligence platform where standard is not compliance but excellence — producing outcomes that are not merely correct but superior, robust, and strategically insightful. Every line of code and every analytic view is built to enterprise-grade quality, thinking beyond immediate tasks to deliver market-leading clarity, predictive power, and decision-making precision.”**
Use these statements to ground every metric, workflow, and AI-assisted insight in ContosoTeamStats. They reinforce the fintech-grade mission, proactive hardening, and expectation that automation yields measurable strategic clarity.

## Documentation & Streamlit roadmap

1. **Documentation hierarchy** – Keep `README.md` as the entry point and link it here, so teammates can immediately access the detailed analytics/Streamlit expectations below.
2. **Design system orientation** – Apply the `ABACO_THEME` palette, typography, and CSS constants throughout the Streamlit canvas; ensure every Plotly figure calls a unified `apply_theme()` to override default blues/greens.
3. **Streamlit pipeline**
   - **Environment setup**: build a cell that handles file uploads, loads Google Fonts, exposes validation widgets, supports reruns without duplication, normalizes column names (lowercase, underscores, no special characters), strips currency/percent symbols before numeric conversion, records ingestion state (shapes/flags), and raises informative errors if the core loan dataset is missing.
   - **KPI calculations**: compute all key financial views (LTV, DTI, delinquency, yield, roll rates, etc.), allow grouping/segmentation across any available column, capture an alerts DataFrame (variable, value, probability), and ensure each analytic cell checks data availability before executing.
   - **Growth & marketing analysis**: surface current portfolio metrics, accept user-defined targets via widgets, calculate the gap, derive a projected growth path with monthly interpolation, and render a Plotly treemap plus aggregated headline metrics.
   - **Roll rate / cascade**: compute DPD transition matrices once base DPD data exists, populate alerts/outlier context, and store structured outputs for downstream dashboards.
   - **Data quality audit**: score missing or zero-row tables, handle absent columns gracefully, and provide robust error messages while continuing to execute other sections when safe.
   - **AI integration**: conditionally activate Gemini/Copilot-style summarization when credentials/libraries exist; otherwise fall back to deterministic rule-based summaries and prompts. Always provide a top-line summary section describing the main insights and actions.
   - **Export & Figma prep**: create flattened fact tables that list dimensions and metrics, ready for export (e.g., referencing <https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/Create-Dark-Editable-Slides?node-id=0-1&t=8coqxRUeoQvNvavm-1>). Provide widgets to refresh ingestion without restarting the runtime.
Every cell should include an English markdown explanation describing its purpose. Operate solely on real uploaded data; never insert placeholder datasets. The combined documentation and Streamlit blueprint keep the analytics delivery aligned with your enterprise-grade standards and the master prompt you shared earlier.
