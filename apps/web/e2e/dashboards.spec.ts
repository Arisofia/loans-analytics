import { test, expect } from '@playwright/test'

test.describe('Dashboard Smoke Tests', () => {
  test('Board dashboard', async ({ page }) => {
    await page.goto('/board', { waitUntil: 'networkidle' })
    await expect(page.getByTestId('dashboard-board')).toBeVisible()
  })

  test('Analytics dashboard', async ({ page }) => {
    await page.goto('/analytics', { waitUntil: 'networkidle' })
    await expect(page.getByTestId('dashboard-analytics')).toBeVisible()
  })

  test('CFO dashboard', async ({ page }) => {
    await page.goto('/cfo', { waitUntil: 'networkidle' })
    await expect(page.getByTestId('dashboard-cfo')).toBeVisible()
  })

  test('Risk dashboard', async ({ page }) => {
    await page.goto('/risk', { waitUntil: 'networkidle' })
    await expect(page.getByTestId('dashboard-risk')).toBeVisible()
  })

  test('Growth dashboard', async ({ page }) => {
    await page.goto('/growth', { waitUntil: 'networkidle' })
    await expect(page.getByTestId('dashboard-growth')).toBeVisible()
  })
})
