const { createClient } = require('@supabase/supabase-js');
const fetch = require('node-fetch'); // Import node-fetch for direct HTTP requests

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function checkKpiValuesTable() {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    console.error('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables.');
    process.exit(1);
  }

  // Ensure node-fetch is available if not already globally present (Node.js < 18)
  if (typeof globalThis.fetch === 'undefined') {
    globalThis.fetch = fetch;
  }

  // Create an admin client (useful for other operations, but not for direct REST API calls in this specific case)
  const adminClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

  try {
    // Directly use fetch to query the Supabase REST API for information_schema.tables
    // Filter for table_schema and table_name
    const restUrl = `${SUPABASE_URL}/rest/v1/information_schema.tables?table_schema=eq.monitoring&table_name=eq.kpi_values&select=table_name`;

    const response = await fetch(restUrl, {
      method: 'GET',
      headers: {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Error querying Supabase REST API: ${response.status} - ${errorText}`);
      process.exit(1);
    }

    const data = await response.json();

    if (data && data.length > 0) {
      console.log('✅ Table monitoring.kpi_values EXISTS (via REST API).');
    } else {
      console.log('❌ Table monitoring.kpi_values DOES NOT EXIST (via REST API).');
    }

  } catch (err) {
    console.error('An unexpected error occurred:', err.message);
    process.exit(1);
  }
}

checkKpiValuesTable();