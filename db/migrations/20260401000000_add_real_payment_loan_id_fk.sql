-- Migration: Add foreign key from real_payment.loan_id to loan_data.loan_id
-- Purpose   : Enforce referential integrity between payment records and loans.
-- Phase 3   : Production Readiness Audit — data model hardening.
--
-- NOTE: Existing data must satisfy the FK before applying in production.
-- Run data quality check first:
--   SELECT DISTINCT loan_id FROM real_payment
--   WHERE loan_id NOT IN (SELECT loan_id FROM loan_data);
-- All returned rows must be cleaned / backfilled before applying this migration.

BEGIN;

-- Ensure loan_data.loan_id is unique (required for FK target).
CREATE UNIQUE INDEX IF NOT EXISTS uq_loan_data_loan_id
    ON public.loan_data (loan_id);

-- Add the FK constraint with DEFERRABLE INITIALLY DEFERRED to allow bulk
-- inserts that arrive out of order within a transaction.
ALTER TABLE public.real_payment
    ADD CONSTRAINT fk_real_payment_loan_id
    FOREIGN KEY (loan_id)
    REFERENCES public.loan_data (loan_id)
    ON DELETE CASCADE
    DEFERRABLE INITIALLY DEFERRED;

COMMIT;
