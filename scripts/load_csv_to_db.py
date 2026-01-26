import logging
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.paths import Paths

DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for load_csv_to_db")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)

def load_data():
    data_dir = Paths.data_dir() / "abaco"

    # Files
    customer_file = data_dir / "customer_data.csv"
    loan_file = data_dir / "loan_data.csv"
    payment_file = data_dir / "real_payment.csv"

    print("Connecting to database...")
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            # Clean existing data
            print("Cleaning existing data...")
            cur.execute("TRUNCATE TABLE real_payment, loan_data, customer_data CASCADE;")

            # 1. Load Customers
            print(f"Loading {customer_file.name}...")
            df_cust = pd.read_csv(customer_file)

            # Map columns
            cust_mapping = {
                "Customer ID": "customer_id",
                "Client Type": "customer_type",
                "Income": "income",
                "Income Currency": "currency",
                "Gender": "gender",
                "Birth Year": "birth_date",
                "Sales Channel": "channel_type",
                "Number of Dependents": "dependents",
                "Location City": "geography_city",
                "Location State Province": "geography_state",
                "Location Country": "geography_country",
                "segment": "segment",
                "subcategoria_linea": "subcategoria_linea",
                "kam_id": "kam_id",
                "Industry": "industry",
            }

            df_cust_mapped = df_cust[list(cust_mapping.keys())].rename(columns=cust_mapping)

            # Deduplicate customers as there might be multiple loans per customer in the CSV
            df_cust_mapped = df_cust_mapped.drop_duplicates(subset=["customer_id"])

            # Handle birth_date (Year to Date)
            df_cust_mapped["birth_date"] = pd.to_datetime(
                df_cust_mapped["birth_date"].astype(str) + "-01-01", errors="coerce"
            ).dt.date

            # Replace NaN/NaT with None for SQL NULL
            df_cust_mapped = df_cust_mapped.astype(object).where(pd.notnull(df_cust_mapped), None)

            # Insert
            cols = list(df_cust_mapped.columns)
            col_names = ", ".join(cols)
            placeholders = ", ".join([f"%({col})s" for col in cols])
            query = f"INSERT INTO customer_data ({col_names}) VALUES ({placeholders})"
            for i, row in enumerate(df_cust_mapped.itertuples(index=False, name=None)):
                try:
                    row_dict = dict(zip(cols, row))
                    cur.execute(query, row_dict)
                except Exception as e:
                    print(f"Failed at row {i}: {row}")
                    raise e

            print(f"Inserted {len(df_cust_mapped)} customers.")

            # 2. Load Loans
            print(f"Loading {loan_file.name}...")
            df_loan = pd.read_csv(loan_file)

            df_loan_mapping = {
                "Loan ID": "loan_id",
                "Customer ID": "customer_id",
                "Product Type": "product_type",
                "Disbursement Date": "disbursement_date",
                "Disbursement Amount": "disbursement_amount",
                "Origination Fee": "origination_fee",
                "Origination Fee Taxes": "origination_fee_taxes",
                "Loan Currency": "currency",
                "Interest Rate APR": "interest_rate_apr",
                "Term": "term",
                "Term Unit": "term_unit",
                "Payment Frequency": "payment_frequency",
                "Days in Default": "days_past_due",
                "Outstanding Loan Value": "outstanding_loan_value",
                "Loan Status": "loan_status",
            }

            df_loan_mapped = df_loan[list(df_loan_mapping.keys())].rename(columns=df_loan_mapping)

            # Filter loans where customer_id exists in customer_data
            valid_customer_ids = set(df_cust_mapped["customer_id"])
            df_loan_mapped = df_loan_mapped[df_loan_mapped["customer_id"].isin(valid_customer_ids)]

            # Handle dates
            df_loan_mapped["disbursement_date"] = pd.to_datetime(
                df_loan_mapped["disbursement_date"], errors="coerce"
            ).dt.date

            # Replace NaN/NaT
            df_loan_mapped = df_loan_mapped.astype(object).where(pd.notnull(df_loan_mapped), None)

            # Insert
            cols = list(df_loan_mapped.columns)
            col_names = ", ".join(cols)
            placeholders = ", ".join([f"%({col})s" for col in cols])
            query = f"INSERT INTO loan_data ({col_names}) VALUES ({placeholders})"
            for i, row in enumerate(df_loan_mapped.itertuples(index=False, name=None)):
                try:
                    row_dict = dict(zip(cols, row))
                    cur.execute(query, row_dict)
                except Exception as e:
                    print(f"Failed at row {i}: {row}")
                    raise e

            print(f"Inserted {len(df_loan_mapped)} loans.")

            # 3. Load Payments
            print(f"Loading {payment_file.name}...")
            df_pay = pd.read_csv(payment_file)

            pay_mapping = {
                "Loan ID": "loan_id",
                "True Payment Date": "true_payment_date",
                "True Principal Payment": "true_principal_payment",
                "True Interest Payment": "true_interest_payment",
                "True Fee Payment": "true_fee_payment",
                "True Other Payment": "true_other_payment",
                "True Tax Payment": "true_tax_payment",
                "True Fee Tax Payment": "true_fee_tax_payment",
                "True Rabates": "true_rebates",
            }

            df_pay_mapped = df_pay[list(pay_mapping.keys())].rename(columns=pay_mapping)

            # Filter payments where loan_id exists in loan_data
            valid_loan_ids = set(df_loan_mapped["loan_id"])
            df_pay_mapped = df_pay_mapped[df_pay_mapped["loan_id"].isin(valid_loan_ids)]

            # Handle dates
            df_pay_mapped["true_payment_date"] = pd.to_datetime(
                df_pay_mapped["true_payment_date"], errors="coerce"
            ).dt.date

            # Replace NaN/NaT
            df_pay_mapped = df_pay_mapped.astype(object).where(pd.notnull(df_pay_mapped), None)

            # Insert
            cols = list(df_pay_mapped.columns)
            col_names = ", ".join(cols)
            placeholders = ", ".join([f"%({col})s" for col in cols])
            query = f"INSERT INTO real_payment ({col_names}) VALUES ({placeholders})"
            for i, row in enumerate(df_pay_mapped.itertuples(index=False, name=None)):
                try:
                    row_dict = dict(zip(cols, row))
                    cur.execute(query, row_dict)
                except Exception as e:
                    print(f"Failed at row {i}: {row}")
                    raise e

            print(f"Inserted {len(df_pay_mapped)} payments.")

        conn.commit()
    print("Data loading complete.")


if __name__ == "__main__":
    load_data()
