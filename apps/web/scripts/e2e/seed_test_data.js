/*
Seed E2E test user and optional table rows in Supabase.
Requires environment variables:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY (service role key for admin calls)
- E2E_TEST_EMAIL
- E2E_TEST_PASSWORD
Optional:
- E2E_SEED_TABLE (table name to insert rows)
- E2E_SEED_ROWS (JSON array string of rows to insert into E2E_SEED_TABLE)

This script saves state to `playwright/.e2e/seed_state.json` for teardown.
*/

import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const E2E_TEST_EMAIL = process.env.E2E_TEST_EMAIL;
const E2E_TEST_PASSWORD = process.env.E2E_TEST_PASSWORD;
const E2E_SEED_TABLE = process.env.E2E_SEED_TABLE;
const E2E_SEED_ROWS = process.env.E2E_SEED_ROWS; // JSON array string

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  process.exit(2);
}
if (!E2E_TEST_EMAIL || !E2E_TEST_PASSWORD) {
  console.error('Missing E2E_TEST_EMAIL or E2E_TEST_PASSWORD');
  process.exit(2);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

async function main() {
  const stateDir = path.resolve(process.cwd(), 'playwright', '.e2e');
  fs.mkdirSync(stateDir, { recursive: true });
  const stateFile = path.join(stateDir, 'seed_state.json');
  const state = { user: null, inserts: [] };

  console.log('Creating test user...');
  try {
    const { data: user, error: createErr } = await supabase.auth.admin.createUser({
      email: E2E_TEST_EMAIL,
      password: E2E_TEST_PASSWORD,
      email_confirm: true,
    });
    if (createErr) throw createErr;
    state.user = { id: user.id, email: user.email };
    console.log('Created user:', state.user);
  } catch (err) {
    console.error('Failed to create user:', err.message || err);
    process.exit(1);
  }

  if (E2E_SEED_TABLE && E2E_SEED_ROWS) {
    console.log(`Seeding table ${E2E_SEED_TABLE} ...`);
    let rows;
    try {
      rows = JSON.parse(E2E_SEED_ROWS);
      if (!Array.isArray(rows)) throw new Error('E2E_SEED_ROWS must be a JSON array');
    } catch (err) {
      console.error('Invalid E2E_SEED_ROWS JSON:', err.message || err);
      process.exit(1);
    }

    try {
      const { data: inserts, error: insertErr } = await supabase.from(E2E_SEED_TABLE).insert(rows).select();
      if (insertErr) throw insertErr;
      state.inserts = inserts.map((r) => ({ table: E2E_SEED_TABLE, id: r.id }));
      console.log('Inserted rows:', state.inserts);
    } catch (err) {
      console.error('Failed to insert rows:', err.message || err);
      process.exit(1);
    }
  }

  fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
  console.log('Seed state written to', stateFile);
}

main().catch((e) => {
  console.error('Unhandled error in seed script', e);
  process.exit(1);
});
