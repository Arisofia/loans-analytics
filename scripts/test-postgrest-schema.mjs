#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js'
import fetch from 'node-fetch'

const supabaseUrl = process.env.SUPABASE_URL
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !serviceRoleKey) {
  console.error('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

async function testPostgrestSchema() {
  console.log('🔍 Testing PostgREST schema access via direct API...\n')

  // The Supabase JS SDK might not expose the schema parameter properly
  // Let's try using the PostgREST API directly

  console.log('Test 1: PostgREST direct API with schema parameter...')
  const postgRestUrl = `${supabaseUrl.replace(/\/$/, '')}/rest/v1`

  // Try the standard PostgREST URL with explicit schema selection
  const kpiValuesUrl = `${postgRestUrl}/kpi_values?select=*&limit=1`
  const kpiDefinitionsUrl = `${postgRestUrl}/monitoring.kpi_definitions?select=*&limit=1`

  console.log(
    `ℹ️  Endpoint 1: GET ${postgRestUrl}/kpi_values (should fail - public schema)`
  )
  const resp1 = await fetch(kpiValuesUrl, {
    headers: {
      Authorization: `Bearer ${serviceRoleKey}`,
      Accept: 'application/json',
    },
  })
  console.log(`   Status: ${resp1.status}`)
  const data1 = await resp1.json()
  if (resp1.ok) {
    console.log(`   ✅ Got ${Array.isArray(data1) ? data1.length : 0} rows`)
  } else {
    console.log(`   ❌ Error: ${data1.message || JSON.stringify(data1)}`)
  }

  console.log(
    `\nℹ️  Endpoint 2: GET ${postgRestUrl}/monitoring.kpi_definitions`
  )
  const resp2 = await fetch(kpiDefinitionsUrl, {
    headers: {
      Authorization: `Bearer ${serviceRoleKey}`,
      Accept: 'application/json',
    },
  })
  console.log(`   Status: ${resp2.status}`)
  const data2 = await resp2.json()
  if (resp2.ok) {
    console.log(`   ✅ Got ${Array.isArray(data2) ? data2.length : 0} rows`)
  } else {
    console.log(`   ❌ Error: ${data2.message || JSON.stringify(data2)}`)
  }

  // Test 3: Try with x-schema header (PostgREST proprietary)
  console.log(`\nTest 2: PostgREST with x-schema header (if supported)...`)
  const resp3 = await fetch(`${postgRestUrl}/kpi_values?select=*&limit=1`, {
    headers: {
      Authorization: `Bearer ${serviceRoleKey}`,
      Accept: 'application/json',
      'x-schema': 'monitoring',
    },
  })
  console.log(`   Status: ${resp3.status}`)
  const data3 = await resp3.json()
  if (resp3.ok) {
    console.log(`   ✅ Got ${Array.isArray(data3) ? data3.length : 0} rows`)
  } else {
    console.log(`   ⚠️  Error: ${data3.message || JSON.stringify(data3)}`)
  }
}

testPostgrestSchema().catch(console.error)
