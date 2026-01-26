import pandas as pd

# Load CSVs (adapt paths):
payment_schedule = pd.read_csv("data/input/Loan_Tape_Payment_Schedule.csv")
collateral = pd.read_csv("data/input/Loan_Tape_Collateral.csv")
historic_payments = pd.read_csv("data/input/Loan_Tape_Historic_Real_Payment.csv")
loan_data = pd.read_csv("data/input/Loan_Tape_Loan_Data.csv")
customer_data = pd.read_csv("data/input/Loan_Tape_Customer_Data.csv")

# Basic stats:
print("Payment Schedule Stats:\n", payment_schedule.describe())
print("\nCollateral Missing Values:\n", collateral.isnull().sum())

# Check for inconsistencies, e.g., match Loan IDs across tables:
common_loans = set(loan_data["Loan ID"]).intersection(set(payment_schedule["Loan ID"]))
print(f"Common Loan IDs: {len(common_loans)} / {len(loan_data['Loan ID'].unique())}")

# Financial calculations (e.g., total outstanding):
total_outstanding = loan_data["Outstanding Loan Value"].sum()
print(f"Total Outstanding Loans: ${total_outstanding:,.2f}")

# Export to JSON for repo's AI agents:
loan_data.to_json("data/metrics/loan_summary.json", orient="records")
