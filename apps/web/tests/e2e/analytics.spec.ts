import { test, expect } from '@playwright/test'

test.describe('Analytics Dashboard', () => {
  test('should load real KPI data from the backend', async ({ page }) => {
    test.setTimeout(15000)
    await page.goto('/analytics')

    await expect(
      page.getByRole('heading', { name: 'Portfolio performance dashboard' })
    ).toBeVisible()

    await expect(page.getByText('Executive Summary', { exact: true })).toBeVisible()
    await expect(page.getByText('Risk & Health', { exact: true })).toBeVisible()
    await expect(page.getByText('Pricing', { exact: true })).toBeVisible()

    // Check for KPI values
    await expect(page.getByText('3.00%')).toBeVisible()
    await expect(page.getByText('1.00%')).toBeVisible()
    await expect(page.getByText('0.00%')).toBeVisible()
  })


  test('should have a working link back to home', async ({ page }) => {
    await page.goto('/analytics')
    await page.getByRole('link', { name: 'Back to homepage' }).click()
    await expect(page).toHaveURL('/')
    await expect(
      page.getByRole('heading', { name: 'Abaco Loans Analytics', exact: true })
    ).toBeVisible()
  })
})
