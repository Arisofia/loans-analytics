import { test as setup, expect } from '@playwright/test'
import dotenv from 'dotenv'
import path from 'path'
import { TestDataManager } from './lib/db-utils'

// Load env from repo root .env.local (adjust path if needed)
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') })

const authFile = 'playwright/.auth/user.json'

setup('prepare DB, authenticate user and save storage state', async ({ page }) => {
  const email = process.env.E2E_TEST_EMAIL || ''
  const password = process.env.E2E_TEST_PASSWORD || ''

  if (!email || !password) {
    throw new Error('E2E_TEST_EMAIL and E2E_TEST_PASSWORD must be set in .env.local')
  }

  // --- FASE 1: DB SEEDING (Backend) ---
  const userId = await TestDataManager.ensureTestUser(email, password)
  await TestDataManager.resetUserData(userId)
  await TestDataManager.seedInitialData(userId)

  // --- FASE 2: UI LOGIN (Frontend) ---
  await page.goto('http://localhost:3000/login')

  // Adjust selectors to match your real UI
  await page.getByPlaceholder(/email/i).fill(email)
  await page.getByPlaceholder(/password/i).fill(password)
  await page.getByRole('button', { name: /iniciar|sign in|login/i }).click()

  // Wait for navigation to protected area
  await expect(page).toHaveURL(/.*dashboard/)

  // Ensure storage dir exists and save state
  await page.context().storageState({ path: authFile })
})
