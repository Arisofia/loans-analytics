import streamlit as st
from backend.python.config.theme import ABACO_THEME
from backend.python.logging_config import get_logger

logger = get_logger(__name__)

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
