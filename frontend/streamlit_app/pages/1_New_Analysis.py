import streamlit as st
from backend.python.config.theme import ANALYTICS_THEME
from backend.python.logging_config import get_logger
logger = get_logger(__name__)
st.set_page_config(page_title='New Analysis', layout='wide')
FONT_IMPORT_URL = 'https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900&family=Poppins:wght@100;200;300;400;500;600;700&display=swap'
st.markdown(f"""\n<style>\n    @import url("{FONT_IMPORT_URL}");\n    .main {{\n        background-color: {ANALYTICS_THEME['colors']['background']};\n        color: {ANALYTICS_THEME['colors']['white']};\n        font-family: '{ANALYTICS_THEME['typography']['primary_font']}', sans-serif;\n    }}\n</style>\n""", unsafe_allow_html=True)
st.title('Deep Dive Analysis')
st.markdown('This is a new page added to the dashboard.')
st.info('Add your custom charts and logic here.')
