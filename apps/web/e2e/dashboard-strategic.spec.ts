import { test, expect } from '@playwright/test'

test('Strategic dashboard smoke', async ({ page }) => {
  await page.goto('/dashboard/strategic', { waitUntil: 'networkidle' })
  await expect(page.getByTestId('dashboard-strategic')).toBeVisible()
})
