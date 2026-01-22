import { test, expect } from '@playwright/test'

test('Financial dashboard smoke', async ({ page }) => {
  await page.goto('/dashboard/financial', { waitUntil: 'networkidle' })
  await expect(page.getByTestId('dashboard-financial')).toBeVisible()
})
