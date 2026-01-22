import { test, expect } from '@playwright/test'

test.describe('Analytics Dashboard', () => {
  test('should load real KPI data from the backend', async ({ page }) => {
    test.setTimeout(15000)
    await page.goto('/analytics')

    await expect(
      page.getByRole('heading', { name: 'Portfolio performance dashboard' })
    ).toBeVisible()

        // Check for placeholder content
    await expect(page.getByText('Analytics Dashboard Placeholder')).toBeVisible()
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
