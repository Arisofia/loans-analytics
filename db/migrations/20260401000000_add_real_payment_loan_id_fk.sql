-- Migration: 20260401000000_add_real_payment_loan_id_fk.sql
--
-- Adds a foreign key constraint from real_payment.loan_id to loan_data.loan_id.
-- The loan_id column on loan_data is not a primary key (id SERIAL is the PK),
-- so we first add a UNIQUE constraint to loan_data.loan_id to make it a valid
-- FK target, then add the FK on real_payment.
--
-- Safe to run on databases where these constraints already exist:
-- both ALTER statements use IF NOT EXISTS / DO-blocks to be idempotent.

BEGIN;

-- 1. Ensure loan_data.loan_id has a unique constraint so it can be a FK target.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_class      t ON t.oid = c.conrelid
        JOIN   pg_namespace  n ON n.oid = t.relnamespace
        WHERE  n.nspname  = 'public'
          AND  t.relname  = 'loan_data'
          AND  c.contype  = 'u'
          AND  c.conname  = 'uq_loan_data_loan_id'
    ) THEN
        ALTER TABLE public.loan_data
            ADD CONSTRAINT uq_loan_data_loan_id UNIQUE (loan_id);
    END IF;
END;
$$;

-- 2. Add FK from real_payment.loan_id → loan_data.loan_id.
--    ON DELETE SET NULL: orphan payment rows are preserved when a loan is
--    deleted (e.g. data correction), rather than cascading a destructive delete.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_class      t ON t.oid = c.conrelid
        JOIN   pg_namespace  n ON n.oid = t.relnamespace
        WHERE  n.nspname = 'public'
          AND  t.relname = 'real_payment'
          AND  c.contype = 'f'
          AND  c.conname = 'fk_real_payment_loan_id'
    ) THEN
        ALTER TABLE public.real_payment
            ADD CONSTRAINT fk_real_payment_loan_id
            FOREIGN KEY (loan_id)
            REFERENCES public.loan_data (loan_id)
            ON DELETE SET NULL
            DEFERRABLE INITIALLY DEFERRED;
    END IF;
END;
$$;

COMMIT;
