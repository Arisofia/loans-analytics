import streamlit as st
import pandas as pd

def load_growth_data():
    return pd.read_csv('data/abaco_portfolio_calculations.csv')

def main():
    st.title('Growth Dashboard')
    data = load_growth_data()
    st.line_chart(data['Growth'])
    st.dataframe(data)

if __name__ == "__main__":
    main()
