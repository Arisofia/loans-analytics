#!/usr/bin/env node
/**
 * Quick table existence check
 */
import { createClient } from '@supabase/supabase-js'
import { config } from 'dotenv'

config({ path: '.env.local' })

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)

async function checkTable() {
  console.log('\n=== CHECKING TABLE EXISTENCE ===\n')

  const tables = [
    { name: 'kpi_values', schema: 'monitoring' },
    { name: 'kpi_definitions', schema: 'monitoring' },
    { name: 'fact_loans', schema: 'public' },
    { name: 'customer_data', schema: 'public' },
  ]

  for (const { name, schema } of tables) {
    try {
      const { data, error, status } = await supabase
        .from(name)
        .select('*', { count: 'exact', head: true })

      if (error) {
        if (error.code === '42P01' || error.code === 'PGRST116') {
          console.log(`❌ ${schema}.${name.padEnd(25)} - NOT FOUND`)
        } else {
          console.log(
            `⚠️  ${schema}.${name.padEnd(25)} - ${error.code}: ${error.message.substring(0, 50)}`
          )
        }
      } else {
        console.log(
          `✅ ${schema}.${name.padEnd(25)} - EXISTS (${data?.length || 0} rows)`
        )
      }
    } catch (err) {
      console.log(
        `⚠️  ${schema}.${name.padEnd(25)} - ERROR: ${err.message.substring(0, 50)}`
      )
    }
  }

  console.log()
}

checkTable().catch(console.error)
