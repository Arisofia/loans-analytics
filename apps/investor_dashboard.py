import streamlit as st
import pandas as pd

def load_investor_data():
    return pd.read_csv('data/abaco_portfolio_calculations.csv')

def main():
    st.title('Investor Dashboard')
    data = load_investor_data()
    st.bar_chart(data['InvestorReturns'])
    st.dataframe(data)

if __name__ == "__main__":
    main()
