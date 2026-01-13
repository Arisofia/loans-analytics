import { defineConfig, devices } from '@playwright/test';
<<<<<<< HEAD
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env.local') });

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  reporter: 'html',
=======

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'line',
>>>>>>> fix/workflows-lint-fix2
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
<<<<<<< HEAD
      use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
=======
      use: { ...devices['Desktop Chrome'] },
    },
  ],
>>>>>>> fix/workflows-lint-fix2
});
