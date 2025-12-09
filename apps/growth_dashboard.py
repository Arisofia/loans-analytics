import streamlit as st
import pandas as pd

def load_growth_data():
    return pd.read_csv('data/abaco_portfolio_calculations.csv')

def main():
    """
    Display the Growth Dashboard using Streamlit, including a line chart and data table.

    Args:
        None

    Returns:
        None. Renders the dashboard UI in the Streamlit app.
    """
    st.title('Growth Dashboard')
    data = load_growth_data()
    st.line_chart(data['Growth'])
    st.dataframe(data)

if __name__ == "__main__":
    main()
