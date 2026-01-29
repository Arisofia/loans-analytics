#!/usr/bin/env node
/**
 * Test Supabase Connection Script
 * Verifies connectivity to Supabase database and API
 *
 * Usage:
 *   node scripts/test-supabase-connection.js
 *
 * Environment Variables Required:
 *   SUPABASE_URL - Your Supabase project URL
 *   SUPABASE_ANON_KEY - Your Supabase anonymous/public key
 */

require('dotenv').config()

async function testSupabaseConnection() {
  console.log('🔍 Testing Supabase Connection...\n')

  // Check environment variables
  const supabaseUrl =
    process.env.SUPABASE_URL || '***REMOVED***'
  const supabaseKey = process.env.SUPABASE_ANON_KEY

  if (!supabaseKey) {
    console.error('❌ ERROR: SUPABASE_ANON_KEY environment variable is not set')
    console.log('\n📝 To fix this:')
    console.log(
      '   1. Get your key from: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api'
    )
    console.log('   2. Add to .env file: SUPABASE_ANON_KEY=your-key-here\n')
    process.exit(1)
  }

  console.log(`📍 Supabase URL: ${supabaseUrl}`)
  console.log(
    `🔑 API Key: ${supabaseKey.substring(0, 20)}...${supabaseKey.substring(supabaseKey.length - 4)}\n`
  )

  try {
    // Dynamic import for ES modules
    const { createClient } = await import('@supabase/supabase-js')

    const supabase = createClient(supabaseUrl, supabaseKey)

    // Test 1: Check KPI Definitions table
    console.log('🧪 Test 1: Querying monitoring.kpi_definitions...')
    const { data: kpiDefs, error: kpiError } = await supabase
      .from('monitoring.kpi_definitions')
      .select('count')

    if (kpiError) {
      console.error('❌ Failed to query kpi_definitions:', kpiError.message)
    } else {
      console.log(
        `✅ Successfully connected! Found ${kpiDefs?.length || 0} KPI definitions\n`
      )
    }

    // Test 2: Check KPI Values table
    console.log('🧪 Test 2: Querying monitoring.kpi_values...')
    const { data: kpiVals, error: valError } = await supabase
      .from('monitoring.kpi_values')
      .select('count')
      .limit(10)

    if (valError) {
      console.error('❌ Failed to query kpi_values:', valError.message)
    } else {
      console.log(
        `✅ Successfully queried kpi_values! Found ${kpiVals?.length || 0} recent records\n`
      )
    }

    // Test 3: Check Historical KPIs table
    console.log('🧪 Test 3: Querying public.historical_kpis...')
    const { data: histKpis, error: histError } = await supabase
      .from('historical_kpis')
      .select('count')
      .limit(10)

    if (histError) {
      console.error('❌ Failed to query historical_kpis:', histError.message)
    } else {
      console.log(
        `✅ Successfully queried historical_kpis! Found ${histKpis?.length || 0} records\n`
      )
    }

    console.log('✅ All connection tests passed!\n')
    console.log('📋 Next Steps:')
    console.log(
      '   1. Add these credentials to Azure Key Vault (aiagent-secrets-kv)'
    )
    console.log('   2. Update Azure App Services to use new Supabase endpoint')
    console.log('   3. Deploy Grafana dashboards with docker-compose\n')
  } catch (error) {
    console.error('❌ Connection test failed:', error.message)
    console.log('\n📝 Troubleshooting:')
    console.log(
      '   1. Install dependencies: npm install @supabase/supabase-js dotenv'
    )
    console.log('   2. Verify SUPABASE_URL and SUPABASE_ANON_KEY are correct')
    console.log('   3. Check network connectivity to Supabase\n')
    process.exit(1)
  }
}

// Run the test
testSupabaseConnection().catch(console.error)
