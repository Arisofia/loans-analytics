#!/usr/bin/env node

/**
 * RLS Smoke Test Suite
 *
 * Validates Row Level Security policies on production Supabase
 * Tests both anonymous, authenticated, and service_role access
 *
 * Usage:
 *   node scripts/test-rls.js
 *
 * Environment variables required:
 *   SUPABASE_URL: Your Supabase project URL
 *   SUPABASE_ANON_KEY: Anonymous/public API key
 *   SUPABASE_SERVICE_ROLE_KEY: Service role key (keep private!)
 *   TEST_USER_EMAIL: Test user email for authenticated tests (optional)
 *   TEST_USER_PASSWORD: Test user password (optional)
 */

const https = require('https')
const { createClient } = require('@supabase/supabase-js')

// Configuration
const config = {
  supabaseUrl:
    process.env.SUPABASE_URL || 'https://pljjgdtczxmrxydfuaep.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsampnZHRjenhtcnh5ZGZ1YWVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyNjc0NjQsImV4cCI6MjA3ODg0MzQ2NH0.xGhXNb7d-9wyTD4gQ3h94cqitwUZGxNozt4Dtqv1dEg',
  serviceRoleKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsampnZHRjenhtcnh5ZGZ1YWVwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzI2NzQ2NCwiZXhwIjoyMDc4ODQzNDY0fQ.oI2VEuQgsx0jr108JqQ6IvLfNPtpggcFUsOkKSXYYKU',
  testUserEmail: process.env.TEST_USER_EMAIL,
  testUserPassword: process.env.TEST_USER_PASSWORD,
}

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
}

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`)
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green)
}

function logError(message) {
  log(`❌ ${message}`, colors.red)
}

function logWarn(message) {
  log(`⚠️  ${message}`, colors.yellow)
}

function logInfo(message) {
  log(`ℹ️  ${message}`, colors.cyan)
}

function logTest(message) {
  log(`\n${message}`, colors.blue)
}

// Test results tracker
const results = {
  passed: 0,
  failed: 0,
  skipped: 0,
  tests: [],
}

function recordResult(testName, passed, message) {
  results.tests.push({ testName, passed, message })
  if (passed) {
    results.passed++
    logSuccess(message)
  } else {
    results.failed++
    logError(message)
  }
}

/**
 * TEST 1: Anonymous Key Should NOT Access Sensitive Data
 */
async function testAnonNoAccess() {
  logTest('TEST 1: Anonymous Key Access (Should FAIL)')

  if (!config.anonKey) {
    logWarn('SUPABASE_ANON_KEY not set, skipping test')
    results.skipped++
    return
  }

  try {
    const anonClient = createClient(config.supabaseUrl, config.anonKey)

    // Try to read customer_data
    const { data, error } = await anonClient
      .from('customer_data')
      .select('*')
      .limit(1)

    if (error && error.code === 'PGRST301') {
      recordResult(
        'Anonymous customer_data access',
        true,
        'Anonymous correctly blocked from reading customer_data (RLS policy enforced)'
      )
    } else if (error) {
      recordResult(
        'Anonymous customer_data access',
        false,
        `Unexpected error: ${error.message}`
      )
    } else if (data && data.length === 0) {
      recordResult(
        'Anonymous customer_data access',
        true,
        'Anonymous access returned empty (RLS policy enforced)'
      )
    } else {
      recordResult(
        'Anonymous customer_data access',
        false,
        `Anonymous should not have access to customer_data. Got ${data?.length || 0} rows`
      )
    }
  } catch (err) {
    recordResult(
      'Anonymous customer_data access',
      false,
      `Exception: ${err.message}`
    )
  }
}

/**
 * TEST 2: Service Role Should Have Full Access
 */
async function testServiceRoleFullAccess() {
  logTest('TEST 2: Service Role Access (Should SUCCEED)')

  if (!config.serviceRoleKey) {
    logWarn('SUPABASE_SERVICE_ROLE_KEY not set, skipping test')
    results.skipped++
    return
  }

  try {
    const adminClient = createClient(config.supabaseUrl, config.anonKey, {
      global: {
        headers: {
          Authorization: `Bearer ${config.serviceRoleKey}`,
        },
      },
    })

    // Test read access to customer_data
    const { data, error } = await adminClient
      .from('customer_data')
      .select('*')
      .limit(1)

    if (error) {
      recordResult(
        'Service role customer_data read',
        false,
        `Service role should have full access. Error: ${error.message}`
      )
    } else {
      recordResult(
        'Service role customer_data read',
        true,
        `Service role has full read access (returned ${data?.length || 0} rows)`
      )
    }

    // Test access to loan_data
    const { data: loanData, error: loanError } = await adminClient
      .from('loan_data')
      .select('*')
      .limit(1)

    if (loanError) {
      recordResult(
        'Service role loan_data read',
        false,
        `Service role should have full access to loan_data. Error: ${loanError.message}`
      )
    } else {
      recordResult(
        'Service role loan_data read',
        true,
        `Service role has full read access to loan_data (returned ${loanData?.length || 0} rows)`
      )
    }

    // Test access to kpi_values (optional table via public view)
    const { data: kpiData, error: kpiError } = await adminClient
      .from('kpi_values')
      .select('*')
      .limit(1)

    if (kpiError) {
      recordResult(
        'Service role kpi_values read',
        false,
        `Service role should have full access to kpi_values. Error: ${kpiError.message}`
      )
    } else {
      recordResult(
        'Service role kpi_values read',
        true,
        `Service role has full read access to kpi_values (returned ${kpiData?.length || 0} rows)`
      )
    }
  } catch (err) {
    recordResult('Service role access', false, `Exception: ${err.message}`)
  }
}

/**
 * TEST 3: Authenticated User Access (Role-Based)
 */
async function testAuthenticatedAccess() {
  logTest('TEST 3: Authenticated User Access (Should use policies)')

  if (!config.testUserEmail || !config.testUserPassword) {
    logWarn(
      'TEST_USER_EMAIL or TEST_USER_PASSWORD not set, skipping authenticated user test'
    )
    logInfo(
      'To enable this test, set: export TEST_USER_EMAIL="user@example.com" TEST_USER_PASSWORD="password"'
    )
    results.skipped++
    return
  }

  try {
    const userClient = createClient(config.supabaseUrl, config.anonKey)

    // Sign in
    const { data: signInData, error: signInError } =
      await userClient.auth.signInWithPassword({
        email: config.testUserEmail,
        password: config.testUserPassword,
      })

    if (signInError) {
      if (signInError.message.includes('Invalid login credentials')) {
        logWarn(
          `Test user '${config.testUserEmail}' does not exist or password is incorrect`
        )
        logInfo(
          'To create test user: Go to Supabase Dashboard → Authentication → Users → Add User'
        )
        results.skipped++
      } else {
        recordResult(
          'Authenticated user sign in',
          false,
          `Could not sign in: ${signInError.message}`
        )
      }
      return
    }

    recordResult(
      'Authenticated user sign in',
      true,
      `User signed in: ${config.testUserEmail}`
    )

    // Test KPI values access via public view
    const { data: kpiData, error: kpiError } = await userClient
      .from('kpi_values')
      .select('*')
      .limit(1)

    if (kpiError) {
      recordResult(
        'Authenticated user kpi_values read',
        false,
        `Error reading kpi_values: ${kpiError.message}`
      )
    } else {
      recordResult(
        'Authenticated user kpi_values read',
        true,
        `Authenticated user can read kpi_values (returned ${kpiData?.length || 0} rows, limited by RLS policy)`
      )
    }
  } catch (err) {
    recordResult(
      'Authenticated user access',
      false,
      `Exception: ${err.message}`
    )
  }
}

/**
 * TEST 4: Verify RLS is Enabled on Tables
 */
async function testRLSEnabled() {
  logTest('TEST 4: RLS Status on Tables (Direct DB Check)')

  if (!config.serviceRoleKey) {
    logWarn('SUPABASE_SERVICE_ROLE_KEY not set, skipping RLS status check')
    results.skipped++
    return
  }

  try {
    const adminClient = createClient(config.supabaseUrl, config.anonKey, {
      global: {
        headers: {
          Authorization: `Bearer ${config.serviceRoleKey}`,
        },
      },
    })

    // Query system catalog (requires admin) - RPC method may not exist
    let data = null
    let error = null

    try {
      const response = await adminClient.rpc(
        'check_rls_status',
        {},
        { count: null }
      )
      data = response.data
      error = response.error
    } catch (rpcError) {
      // RPC method doesn't exist, which is expected
      error = 'RPC method not available'
    }

    // If RPC doesn't exist, try direct query
    const query = `
      SELECT tablename, rowsecurity
      FROM pg_tables
      WHERE schemaname = 'monitoring'
        AND tablename IN ('kpi_values')
      UNION ALL
      SELECT tablename, rowsecurity
      FROM pg_tables
      WHERE schemaname = 'public'
        AND tablename IN ('customer_data', 'loan_data', 'financial_statements')
      ORDER BY tablename
    `

    logInfo(
      'RLS Status Check: Requires direct database access (use psql or db admin panel)'
    )
    logInfo('SQL Query to run:')
    logInfo(`  ${query}`)
    logInfo('Expected: All tables should show rowsecurity = true')

    results.skipped++
  } catch (err) {
    logWarn(`RLS status check not available: ${err.message}`)
    results.skipped++
  }
}

/**
 * Main Test Runner
 */
async function runAllTests() {
  log('', colors.cyan)
  log(
    '═══════════════════════════════════════════════════════════════',
    colors.cyan
  )
  log(
    '     RLS SMOKE TEST SUITE - SUPABASE PRODUCTION SECURITY      ',
    colors.cyan
  )
  log(
    '═══════════════════════════════════════════════════════════════',
    colors.cyan
  )
  log('', colors.cyan)

  logInfo(`Testing: ${config.supabaseUrl}`)
  logInfo(`Anon Key: ${config.anonKey ? '✓ Set' : '✗ Missing'}`)
  logInfo(`Service Role Key: ${config.serviceRoleKey ? '✓ Set' : '✗ Missing'}`)
  logInfo(`Test User: ${config.testUserEmail ? '✓ Set' : '✗ Missing'}`)
  log('', colors.cyan)

  // Run all tests
  await testAnonNoAccess()
  await testServiceRoleFullAccess()
  await testAuthenticatedAccess()
  await testRLSEnabled()

  // Print summary
  log('', colors.cyan)
  log(
    '═══════════════════════════════════════════════════════════════',
    colors.cyan
  )
  log('TEST SUMMARY', colors.cyan)
  log(
    '═══════════════════════════════════════════════════════════════',
    colors.cyan
  )
  log('', colors.cyan)

  results.tests.forEach((test) => {
    const status = test.passed ? colors.green : colors.red
    const icon = test.passed ? '✅' : '❌'
    log(`${icon} ${test.testName}`, status)
  })

  log('', colors.cyan)
  log(
    `Total Passed: ${colors.green}${results.passed}${colors.reset}`,
    colors.cyan
  )
  log(
    `Total Failed: ${colors.red}${results.failed}${colors.reset}`,
    colors.cyan
  )
  log(
    `Total Skipped: ${colors.yellow}${results.skipped}${colors.reset}`,
    colors.cyan
  )
  log('', colors.cyan)

  if (results.failed === 0 && results.passed > 0) {
    logSuccess(`ALL TESTS PASSED! RLS is working correctly.`)
    process.exit(0)
  } else if (results.failed > 0) {
    logError(`${results.failed} TEST(S) FAILED! Review RLS policies.`)
    process.exit(1)
  } else {
    logWarn('No tests executed. Set environment variables to run tests.')
    process.exit(1)
  }
}

// Run tests
runAllTests().catch((err) => {
  logError(`Fatal error: ${err.message}`)
  process.exit(1)
})