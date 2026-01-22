import { test, expect } from '@playwright/test'

test('Operational dashboard smoke', async ({ page }) => {
  await page.goto('/dashboard/operational', { waitUntil: 'networkidle' })
  await expect(page.getByTestId('dashboard-operational')).toBeVisible()
})
