
const { createClient } = require('@supabase/supabase-js');
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL;
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY || !TEST_USER_EMAIL || !TEST_USER_PASSWORD) {
  console.error('Please set SUPABASE_URL, SUPABASE_ANON_KEY, TEST_USER_EMAIL, and TEST_USER_PASSWORD environment variables.');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function getJwtToken() {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: TEST_USER_EMAIL,
      password: TEST_USER_PASSWORD,
    });

    if (error) {
      console.error('Error signing in:', error.message);
      process.exit(1);
    }

    if (data && data.session && data.session.access_token) {
      console.log(data.session.access_token);
    } else {
      console.error('Failed to retrieve access token.');
      process.exit(1);
    }
  } catch (err) {
    console.error('An unexpected error occurred:', err.message);
    process.exit(1);
  }
}

getJwtToken();
