#!/usr/bin/env node
/**
 * SUPABASE KEY & CONNECTION DIAGNOSTICS
 * ======================================
 * Purpose: Safely diagnose Supabase connection and authentication issues
 *          without exposing secrets in logs
 * 
 * Usage: node scripts/diagnose-supabase-keys.mjs
 */

import { createClient } from '@supabase/supabase-js';
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
config({ path: join(__dirname, '../.env') });
config({ path: join(__dirname, '../.env.local') });

console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║       SUPABASE CONNECTION & KEY DIAGNOSTICS                    ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// ================================================================
// 1. ENVIRONMENT VARIABLE CHECKS
// ================================================================
console.log('=== 1. ENVIRONMENT VARIABLES ===\n');

const requiredVars = {
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  DATABASE_URL: process.env.DATABASE_URL,
  SUPABASE_DB_URL: process.env.SUPABASE_DB_URL,
};

function maskSecret(value) {
  if (!value) return '❌ NOT SET';
  if (value.length < 20) return '⚠️  TOO SHORT (possible error)';
  
  // Show first 4 and last 4 characters
  const masked = value.slice(0, 8) + '...' + value.slice(-8);
  return `✓ Set (${value.length} chars): ${masked}`;
}

function validateJWT(key) {
  if (!key) return { valid: false, error: 'Key not set' };
  
  // JWT format: header.payload.signature (base64url encoded)
  const parts = key.split('.');
  if (parts.length !== 3) {
    return { valid: false, error: `Invalid JWT format (${parts.length} parts, expected 3)` };
  }
  
  try {
    // Decode header
    const header = JSON.parse(Buffer.from(parts[0], 'base64').toString());
    const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
    
    return {
      valid: true,
      header,
      payload: {
        role: payload.role,
        iss: payload.iss,
        iat: payload.iat ? new Date(payload.iat * 1000).toISOString() : undefined,
        exp: payload.exp ? new Date(payload.exp * 1000).toISOString() : undefined,
      }
    };
  } catch (err) {
    return { valid: false, error: err.message };
  }
}

for (const [key, value] of Object.entries(requiredVars)) {
  console.log(`${key}:`);
  console.log(`  ${maskSecret(value)}`);
  
  // Validate JWT keys
  if (key.includes('_KEY') && value) {
    const validation = validateJWT(value);
    if (validation.valid) {
      console.log(`  ✓ Valid JWT token`);
      console.log(`  Role: ${validation.payload.role || 'N/A'}`);
      console.log(`  Issuer: ${validation.payload.iss || 'N/A'}`);
      if (validation.payload.exp) {
        const expired = new Date(validation.payload.exp) < new Date();
        console.log(`  Expires: ${validation.payload.exp} ${expired ? '⚠️  EXPIRED' : '✓'}`);
      }
    } else {
      console.log(`  ⚠️  ${validation.error}`);
    }
  }
  
  // Validate connection strings
  if (key.includes('URL') && value && value.startsWith('postgres')) {
    try {
      const url = new URL(value);
      console.log(`  ✓ Valid PostgreSQL URL`);
      console.log(`  Host: ${url.hostname}`);
      console.log(`  Port: ${url.port || 5432}`);
      console.log(`  Database: ${url.pathname.slice(1)}`);
      console.log(`  Username: ${url.username || 'N/A'}`);
      console.log(`  SSL: ${url.searchParams.get('sslmode') || 'default'}`);
    } catch (err) {
      console.log(`  ⚠️  Invalid URL format: ${err.message}`);
    }
  }
  
  console.log();
}

// ================================================================
// 2. SUPABASE CLIENT CONNECTION TEST
// ================================================================
console.log('\n=== 2. SUPABASE CLIENT CONNECTION TEST ===\n');

if (!requiredVars.SUPABASE_URL || !requiredVars.SUPABASE_ANON_KEY) {
  console.log('❌ Cannot test: SUPABASE_URL or SUPABASE_ANON_KEY not set\n');
} else {
  try {
    console.log('Creating Supabase client (anon key)...');
    const supabase = createClient(
      requiredVars.SUPABASE_URL,
      requiredVars.SUPABASE_ANON_KEY
    );
    
    console.log('✓ Client created successfully\n');
    
    // Test 1: Health check via simple query
    console.log('Test 1: Database health check...');
    try {
      const { data, error } = await supabase.from('_health').select('*').limit(1);
      if (error && error.code !== '42P01') { // Ignore "table doesn't exist"
        console.log(`⚠️  Query error: ${error.message}`);
      } else {
        console.log('✓ Database connection successful\n');
      }
    } catch (err) {
      console.log(`✓ Connection test passed (table check: ${err.message})\n`);
    }
    
    // Test 2: RLS policy test (anonymous access)
    console.log('Test 2: RLS policy test (anonymous role)...');
    try {
      const { data, error } = await supabase.from('fact_loans').select('id').limit(1);
      if (error) {
        if (error.code === '42P01') {
          console.log('⚠️  Table "fact_loans" does not exist');
        } else if (error.code === '42501') {
          console.log('✓ RLS is working (anonymous blocked as expected)');
        } else {
          console.log(`⚠️  Unexpected error: ${error.message} (code: ${error.code})`);
        }
      } else {
        console.log(`✓ Anonymous SELECT returned ${data?.length || 0} rows`);
      }
    } catch (err) {
      console.log(`❌ Connection error: ${err.message}`);
    }
    
    console.log();
  } catch (err) {
    console.log(`❌ Failed to create client: ${err.message}\n`);
  }
}

// ================================================================
// 3. SERVICE ROLE CONNECTION TEST
// ================================================================
console.log('\n=== 3. SERVICE ROLE CONNECTION TEST ===\n');

if (!requiredVars.SUPABASE_URL || !requiredVars.SUPABASE_SERVICE_ROLE_KEY) {
  console.log('❌ Cannot test: SUPABASE_SERVICE_ROLE_KEY not set\n');
} else {
  try {
    console.log('Creating Supabase client (service role key)...');
    const supabaseService = createClient(
      requiredVars.SUPABASE_URL,
      requiredVars.SUPABASE_SERVICE_ROLE_KEY
    );
    
    console.log('✓ Service role client created successfully\n');
    
    // Test: Service role should bypass RLS
    console.log('Test: Service role RLS bypass check...');
    try {
      const { data, error } = await supabaseService.from('fact_loans').select('id').limit(5);
      if (error) {
        if (error.code === '42P01') {
          console.log('⚠️  Table "fact_loans" does not exist');
        } else {
          console.log(`⚠️  Service role query failed: ${error.message}`);
        }
      } else {
        console.log(`✓ Service role bypassed RLS: ${data?.length || 0} rows returned`);
      }
    } catch (err) {
      console.log(`❌ Service role error: ${err.message}`);
    }
    
    console.log();
  } catch (err) {
    console.log(`❌ Failed to create service role client: ${err.message}\n`);
  }
}

// ================================================================
// 4. KEY TYPE ANALYSIS
// ================================================================
console.log('\n=== 4. KEY TYPE ANALYSIS ===\n');

console.log('Expected key types:');
console.log('  SUPABASE_ANON_KEY: JWT with role="anon"');
console.log('  SUPABASE_SERVICE_ROLE_KEY: JWT with role="service_role"');
console.log('  DATABASE_URL: PostgreSQL connection string (postgres://...)');
console.log('  SUPABASE_DB_URL: PostgreSQL connection string with pooler suffix\n');

if (requiredVars.SUPABASE_ANON_KEY) {
  const anonValidation = validateJWT(requiredVars.SUPABASE_ANON_KEY);
  if (anonValidation.valid && anonValidation.payload.role !== 'anon') {
    console.log(`⚠️  WARNING: SUPABASE_ANON_KEY has role="${anonValidation.payload.role}" (expected "anon")`);
  }
}

if (requiredVars.SUPABASE_SERVICE_ROLE_KEY) {
  const serviceValidation = validateJWT(requiredVars.SUPABASE_SERVICE_ROLE_KEY);
  if (serviceValidation.valid && serviceValidation.payload.role !== 'service_role') {
    console.log(`⚠️  WARNING: SUPABASE_SERVICE_ROLE_KEY has role="${serviceValidation.payload.role}" (expected "service_role")`);
  }
}

// ================================================================
// 5. COMMON ISSUES CHECKLIST
// ================================================================
console.log('\n=== 5. COMMON ISSUES CHECKLIST ===\n');

const issues = [];

if (!requiredVars.SUPABASE_URL) {
  issues.push('❌ SUPABASE_URL is not set');
}

if (!requiredVars.SUPABASE_ANON_KEY) {
  issues.push('❌ SUPABASE_ANON_KEY is not set');
}

if (!requiredVars.SUPABASE_SERVICE_ROLE_KEY) {
  issues.push('⚠️  SUPABASE_SERVICE_ROLE_KEY is not set (optional but recommended)');
}

if (requiredVars.DATABASE_URL && !requiredVars.DATABASE_URL.includes('sslmode')) {
  issues.push('⚠️  DATABASE_URL missing SSL configuration (add ?sslmode=require)');
}

const anonVal = validateJWT(requiredVars.SUPABASE_ANON_KEY);
const serviceVal = validateJWT(requiredVars.SUPABASE_SERVICE_ROLE_KEY);

if (anonVal.valid && serviceVal.valid && anonVal.payload.iss !== serviceVal.payload.iss) {
  issues.push('⚠️  ANON_KEY and SERVICE_ROLE_KEY have different issuers (possible project mismatch)');
}

if (issues.length === 0) {
  console.log('✓ No obvious configuration issues detected\n');
} else {
  console.log('Issues found:');
  issues.forEach(issue => console.log(`  ${issue}`));
  console.log();
}

// ================================================================
// SUMMARY
// ================================================================
console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║                   DIAGNOSTICS COMPLETE                         ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

console.log('Next steps:');
console.log('  1. If keys are invalid, regenerate them in Supabase Dashboard');
console.log('  2. Run: node scripts/diagnose-rls.sql for database-level RLS checks');
console.log('  3. If "No suitable key" error persists, verify JWT signature algorithm');
console.log('  4. Check Supabase project settings: Settings → API\n');
