import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'
import path from 'path'

// Load env vars explicitly so this works when run by Playwright/Node
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !serviceRoleKey) {
  throw new Error(
    'Missing SUPABASE_URL (NEXT_PUBLIC_SUPABASE_URL) or SUPABASE_SERVICE_ROLE_KEY in .env.local'
  )
}

const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
})

export const TestDataManager = {
  /**
   * Ensure the test user exists. Returns the user id.
   */
  async ensureTestUser(email: string, password: string): Promise<string> {
    if (!email || !password) throw new Error('E2E test user credentials are required')

    // Try to find existing user by email
    try {
      const listRes = await supabaseAdmin.auth.admin.listUsers()
      const users = listRes?.data?.users ?? listRes?.users ?? []
      const existing = users.find((u) => u.email === email)
      if (existing) return existing.id

      // Create user if not found
      const createRes = await supabaseAdmin.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: { full_name: 'E2E Test Bot' },
      })

      if (createRes.error) throw createRes.error
      return createRes?.data?.user?.id ?? createRes?.user?.id
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      console.error('Error ensuring test user:', message)
      throw err
    }
  },

  /**
   * Delete all data for a user to ensure deterministic state.
   */
  async resetUserData(userId: string) {
    if (!userId) throw new Error('userId is required to reset data')

    // Adjust table names/columns to match your schema
    try {
      const { error: loansError } = await supabaseAdmin.from('loans').delete().eq('user_id', userId)
      if (loansError) throw loansError

      // Add more tables to clean as needed
      // await supabaseAdmin.from('notifications').delete().eq('user_id', userId);

      return true
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      console.error('Error resetting user data:', message)
      throw err
    }
  },

  /**
   * Seed deterministic initial data for tests.
   */
  async seedInitialData(userId: string) {
    if (!userId) throw new Error('userId is required to seed data')

    // Example: two loans (one active, one in default). Adjust schema fields to match your DB.
    const loans = [
      {
        user_id: userId,
        amount: 62000,
        status: 'active',
        term_months: 36,
        interest_rate: 0.05,
        created_at: new Date().toISOString(),
      },
      {
        user_id: userId,
        amount: 10000,
        status: 'default',
        term_months: 12,
        interest_rate: 0.12,
        created_at: new Date().toISOString(),
      },
    ]

    try {
      const { error } = await supabaseAdmin.from('loans').insert(loans)
      if (error) throw error
      return true
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      console.error('Error seeding initial data:', message)
      throw err
    }
  },
}
