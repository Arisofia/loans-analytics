/*
Teardown E2E seeded data created by seed_test_data.js
Reads `playwright/.e2e/seed_state.json` and deletes inserted rows and user.
*/

import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  process.exit(2);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, { auth: { persistSession: false } });

async function main() {
  const stateDir = path.resolve(process.cwd(), 'playwright', '.e2e');
  const stateFile = path.join(stateDir, 'seed_state.json');

  if (!fs.existsSync(stateFile)) {
    console.log('No seed state file found, nothing to teardown.');
    return;
  }

  const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));

  if (Array.isArray(state.inserts) && state.inserts.length > 0) {
    for (const ins of state.inserts) {
      const table = ins.table;
      const id = ins.id;
      try {
        console.log(`Deleting ${table} id=${id}`);
        const { error } = await supabase.from(table).delete().eq('id', id);
        if (error) console.error('Delete error:', error.message || error);
      } catch (err) {
        console.error('Failed deleting row:', err.message || err);
      }
    }
  }

  if (state.user && state.user.id) {
    try {
      console.log('Deleting user', state.user.id);
      const { error } = await supabase.auth.admin.deleteUser(state.user.id);
      if (error) console.error('Delete user error:', error.message || error);
    } catch (err) {
      console.error('Failed deleting user:', err.message || err);
    }
  }

  // Remove state file
  try {
    fs.unlinkSync(stateFile);
    console.log('Removed seed state file');
  } catch (err) {
    console.error('Failed removing state file:', err.message || err);
  }
}

main().catch((e) => {
  console.error('Unhandled error in teardown script', e);
  process.exit(1);
});
