PRIMARY_COLOR = "#0B6EFD"
BACKGROUND_COLOR = "#0F172A"
TEXT_COLOR = "#E2E8F0"
ACCENT_COLOR = "#22C55E"
FONT = "Inter"
PAGE_TITLE = "ABACO AI Operations"
PAGE_ICON = "📊"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
CUSTOM_CSS = f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, {BACKGROUND_COLOR} 0%, #111827 100%);
            color: {TEXT_COLOR};
            font-family: '{FONT}', sans-serif;
        }}
        .metric-card {{
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }}
        .accent {{ color: {ACCENT_COLOR}; }}
    </style>
"""
