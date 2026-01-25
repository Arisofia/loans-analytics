-- Initialization: Create base tables for analytics views

BEGIN;

-- Customer Data
CREATE TABLE IF NOT EXISTS customer_data (
    customer_id TEXT PRIMARY KEY,
    customer_type TEXT,
    income NUMERIC,
    currency TEXT,
    gender TEXT,
    birth_date DATE,
    channel_type TEXT,
    dependents INT,
    geography_city TEXT,
    geography_state TEXT,
    geography_country TEXT,
    segment TEXT,
    subcategoria_linea TEXT,
    kam_id TEXT,
    industry TEXT
);

-- Loan Data
CREATE TABLE IF NOT EXISTS loan_data (
    id SERIAL PRIMARY KEY,
    loan_id TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customer_data(customer_id),
    product_type TEXT,
    disbursement_date DATE NOT NULL,
    disbursement_amount NUMERIC NOT NULL,
    origination_fee NUMERIC,
    origination_fee_taxes NUMERIC,
    currency TEXT,
    interest_rate_apr NUMERIC,
    term INT,
    term_unit TEXT,
    payment_frequency TEXT,
    days_past_due INT DEFAULT 0,
    outstanding_loan_value NUMERIC,
    loan_status TEXT
);

-- Payment Data
CREATE TABLE IF NOT EXISTS real_payment (
    payment_id SERIAL PRIMARY KEY,
    loan_id TEXT NOT NULL,
    true_payment_date DATE NOT NULL,
    true_principal_payment NUMERIC DEFAULT 0,
    true_interest_payment NUMERIC DEFAULT 0,
    true_fee_payment NUMERIC DEFAULT 0,
    true_other_payment NUMERIC DEFAULT 0,
    true_tax_payment NUMERIC DEFAULT 0,
    true_fee_tax_payment NUMERIC DEFAULT 0,
    true_rebates NUMERIC DEFAULT 0
);

CREATE INDEX idx_loan_data_loan_id ON loan_data(loan_id);
CREATE INDEX idx_loan_data_customer_id ON loan_data(customer_id);
CREATE INDEX idx_real_payment_loan_id ON real_payment(loan_id);

COMMIT;
