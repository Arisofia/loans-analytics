-- GDPR Phase 4: Encrypt PII columns at rest in customer_data
-- Uses pgcrypto pgp_sym_encrypt/pgp_sym_decrypt (symmetric AES-256 via GnuPG).
-- The encryption key is injected via the app-level setting 'app.pii_key'.
-- Plaintext PII columns (if any) must be backfilled and then dropped by a DBA
-- once all application reads have been migrated to the encrypted columns.
BEGIN;

-- 1. Enable pgcrypto (idempotent on Supabase/Postgres 14+)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Add encrypted PII columns (stored as BYTEA).
--    These hold: full_name, email, phone, national_id.
--    Existing rows will have NULL; application layer must write encrypted values
--    on next upsert.
ALTER TABLE public.customer_data
    ADD COLUMN IF NOT EXISTS full_name_enc   BYTEA,
    ADD COLUMN IF NOT EXISTS email_enc       BYTEA,
    ADD COLUMN IF NOT EXISTS phone_enc       BYTEA,
    ADD COLUMN IF NOT EXISTS national_id_enc BYTEA;

-- 3. Encrypt birth_date as text in a separate column so the original DATE column
--    remains available for age-band analytics (no direct PII in plaintext form).
ALTER TABLE public.customer_data
    ADD COLUMN IF NOT EXISTS birth_date_enc BYTEA;

-- 4. Helper function: encrypt a plaintext value using the session key.
--    Usage: SELECT pii_encrypt('plain text');
--    Key must be set per session: SET app.pii_key = '<secret>';
CREATE OR REPLACE FUNCTION public.pii_encrypt(plaintext TEXT)
RETURNS BYTEA
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    RETURN pgp_sym_encrypt(
        plaintext,
        current_setting('app.pii_key'),
        'compress-algo=1, cipher-algo=aes256'
    );
END;
$$;

-- 5. Helper function: decrypt a PII column value.
--    Usage: SELECT pii_decrypt(email_enc) FROM customer_data WHERE ...;
CREATE OR REPLACE FUNCTION public.pii_decrypt(ciphertext BYTEA)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF ciphertext IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN pgp_sym_decrypt(
        ciphertext,
        current_setting('app.pii_key')
    );
END;
$$;

-- 6. Restrict helper functions to service_role only.
REVOKE ALL ON FUNCTION public.pii_encrypt(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.pii_decrypt(BYTEA) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.pii_encrypt(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.pii_decrypt(BYTEA) TO service_role;

-- 7. Decrypted view for internal analytics queries (service_role only).
--    Consumers must SET app.pii_key before querying this view.
CREATE OR REPLACE VIEW public.customer_data_pii AS
SELECT
    customer_id,
    customer_type,
    income,
    currency,
    gender,
    birth_date,
    channel_type,
    dependents,
    geography_city,
    geography_state,
    geography_country,
    segment,
    subcategoria_linea,
    kam_id,
    industry,
    public.pii_decrypt(full_name_enc)   AS full_name,
    public.pii_decrypt(email_enc)       AS email,
    public.pii_decrypt(phone_enc)       AS phone,
    public.pii_decrypt(national_id_enc) AS national_id
FROM public.customer_data;

-- Restrict the PII view to service_role.
REVOKE ALL ON public.customer_data_pii FROM PUBLIC;
GRANT SELECT ON public.customer_data_pii TO service_role;

COMMENT ON COLUMN public.customer_data.full_name_enc   IS 'AES-256 pgcrypto encrypted full name (GDPR Art.32)';
COMMENT ON COLUMN public.customer_data.email_enc       IS 'AES-256 pgcrypto encrypted email (GDPR Art.32)';
COMMENT ON COLUMN public.customer_data.phone_enc       IS 'AES-256 pgcrypto encrypted phone number (GDPR Art.32)';
COMMENT ON COLUMN public.customer_data.national_id_enc IS 'AES-256 pgcrypto encrypted national ID (GDPR Art.32)';
COMMENT ON COLUMN public.customer_data.birth_date_enc  IS 'AES-256 pgcrypto encrypted birth date text (GDPR Art.32)';

COMMIT;
