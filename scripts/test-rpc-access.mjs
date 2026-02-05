#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !serviceRoleKey) {
  console.error('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

const client = createClient(supabaseUrl, serviceRoleKey)

async function testRpcAccess() {
  console.log('🔍 Testing RPC-based access to monitoring schema...\n')

  // Create a simple RPC function that returns monitoring data
  // We'll use the `sql` function if available, or fall back to a custom RPC

  console.log(
    'Test 1: Using rpc() with JSON function to access monitoring schema...'
  )
  const { data: rpcData, error: rpcError } = await client.rpc(
    'get_schema_info',
    {
      schema_name: 'monitoring',
    }
  )

  if (rpcError?.message?.includes('does not exist')) {
    console.log(`❌ Custom RPC not available. Trying alternative approach...`)
  } else if (rpcError) {
    console.log(`⚠️  Error: ${rpcError.message}`)
  } else {
    console.log(`✅ RPC succeeded: ${JSON.stringify(rpcData)}`)
  }

  // Test 2: Try to use table access with fully qualified name as a query parameter
  console.log(
    '\nTest 2: Direct .from() with monitoring.kpi_values (checking supabase-js version)...'
  )
  const pkg = await import('../package.json', { assert: { type: 'json' } })
  console.log(
    `ℹ️  supabase-js version: ${pkg.default?.dependencies['@supabase/supabase-js']}`
  )

  // Test if schema parameter is documented in source
  console.log(
    '\nTest 3: Checking if schema parameter works with a simple table name...'
  )
  const testTable = 'kpi_definitions'
  const testSchema = 'monitoring'

  try {
    console.log(
      `ℹ️  Attempting: client.from('${testTable}', { schema: '${testSchema}' })`
    )
    const builder = client.from(testTable, { schema: testSchema })
    console.log(`✅ Query builder created successfully`)
    console.log(`   Builder: ${builder.toString()}`)

    const { data, error } = await builder.select('*').limit(1)
    if (error) {
      console.log(`❌ Query failed: ${error.message}`)
    } else {
      console.log(`✅ Query succeeded! Got ${data?.length || 0} rows`)
    }
  } catch (e) {
    console.log(`❌ Exception: ${e.message}`)
  }
}

testRpcAccess().catch(console.error)
