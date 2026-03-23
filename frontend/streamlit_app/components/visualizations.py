from backend.python.config.theme import ABACO_THEME

def apply_theme(fig):
    fig.update_layout(plot_bgcolor=ABACO_THEME['colors']['background'], paper_bgcolor=ABACO_THEME['colors']['background'], font_color=ABACO_THEME['colors']['light_gray'], title_font_color=ABACO_THEME['colors']['primary_purple'], colorway=['#C1A6FF', '#5F4896', '#10B981', '#FB923C'])
    return fig

def styled_df(df):
    return df.style.set_table_styles([{'selector': 'tr:hover', 'props': [('background-color', ABACO_THEME['colors']['medium_gray'])]}])
