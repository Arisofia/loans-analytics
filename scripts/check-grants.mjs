#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !serviceRoleKey) {
  console.error('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

const client = createClient(supabaseUrl, serviceRoleKey)

async function checkMonitoringGrants() {
  console.log('🔍 Checking monitoring schema access...\n')

  // Test 1: Direct table access
  console.log('Test 1: Attempting direct access to monitoring.kpi_values...')
  const { data: data1, error: error1 } = await client
    .from('kpi_values', { schema: 'monitoring' })
    .select('*')
    .limit(1)

  if (error1) {
    console.log(`❌ Error: ${error1.message}`)
    console.log(`   Details: ${JSON.stringify(error1)}`)
  } else {
    console.log(`✅ Success! Retrieved ${data1?.length || 0} rows`)
  }

  // Test 2: Check if schema even exists
  console.log(
    '\nTest 2: Checking if monitoring schema exists via information_schema...'
  )
  const { data: schemaCheck, error: schemaError } = await client.rpc(
    'query_schema',
    { schema_name: 'monitoring' },
    { count: 'exact' }
  )

  if (schemaError?.message?.includes('does not exist')) {
    console.log('❌ No such function. Will try alternative approach.')
  } else if (schemaError) {
    console.log(`⚠️  RPC failed: ${schemaError.message}`)
  } else {
    console.log(`✅ RPC succeeded`)
  }

  // Test 3: Try accessing with explicit schema prefix
  console.log('\nTest 3: Attempting with raw SQL via RPC...')
  const { data: rawData, error: rawError } = await client
    .rpc('sql', {
      sql: 'SELECT COUNT(*) as count FROM monitoring.kpi_values LIMIT 1',
    })
    .catch((e) => ({ data: null, error: e }))

  if (rawError) {
    console.log(`⚠️  RPC sql() not available`)
  } else if (rawData) {
    console.log(`✅ Raw SQL succeeded: ${JSON.stringify(rawData)}`)
  }

  // Test 4: List available functions
  console.log('\nTest 4: Checking information_schema for table privileges...')
  const { data: privData, error: privError } = await client
    .from('information_schema.table_privileges', {
      schema: 'information_schema',
    })
    .select('*')
    .eq('table_schema', 'monitoring')
    .eq('table_name', 'kpi_values')
    .limit(5)

  if (privError) {
    console.log(`❌ Query result: ${privError.message}`)
  } else {
    if (privData && privData.length > 0) {
      console.log(`✅ Found ${privData.length} privilege entries:`)
      privData.forEach((p) => {
        console.log(`   - ${p.grantee}: ${p.privilege_type}`)
      })
    } else {
      console.log(
        `⚠️  No privilege entries found (may indicate missing grants)`
      )
    }
  }
}

checkMonitoringGrants().catch(console.error)
