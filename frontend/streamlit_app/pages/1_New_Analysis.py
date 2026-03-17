import sys
from pathlib import Path

import streamlit as st

# Add repository root to sys.path to ensure correct module resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent  # Adjusted path for pages
for _p in (ROOT_DIR / "backend", ROOT_DIR / "frontend", ROOT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from python.config.theme import ABACO_THEME  # noqa: E402
from python.logging_config import get_logger  # noqa: E402

logger = get_logger(__name__)

# Robust Bootstrap Import (if needed for individual page execution)
try:
    from streamlit_app.bootstrap import bootstrap_repo_root

    bootstrap_repo_root()
except ImportError:
    logger.info("Bootstrap module not available; proceeding without repo bootstrap.")

st.set_page_config(page_title="New Analysis", layout="wide")
# Apply custom CSS using ABACO_THEME
FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900"
    "&family=Poppins:wght@100;200;300;400;500;600;700&display=swap"
)
st.markdown(
    f"""
<style>
    @import url("{FONT_IMPORT_URL}");
    .main {{
        background-color: {ABACO_THEME['colors']['background']};
        color: {ABACO_THEME['colors']['white']};
        font-family: '{ABACO_THEME['typography']['primary_font']}', sans-serif;
    }}
</style>
""",
    unsafe_allow_html=True,
)
st.title("Deep Dive Analysis")  # Removed emoji
st.markdown("This is a new page added to the dashboard.")
# Example content
st.info("Add your custom charts and logic here.")
