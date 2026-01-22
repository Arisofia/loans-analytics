import { defineConfig, devices } from '@playwright/test'
import dotenv from 'dotenv'
import path from 'path'

dotenv.config({ path: path.resolve(__dirname, '.env.local') })

const PORT = Number(process.env.E2E_PORT ?? '3000')

export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/smoke.spec.ts', '**/dashboards.spec.ts'],
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: process.env.CI
      ? `E2E_BYPASS_AUTH=1 npm run build && E2E_BYPASS_AUTH=1 npm run start -- -p ${PORT}`
      : `E2E_BYPASS_AUTH=1 npm run dev -- -p ${PORT}`,
    port: PORT,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
