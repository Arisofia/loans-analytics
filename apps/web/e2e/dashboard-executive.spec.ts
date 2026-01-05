import { test, expect } from '@playwright/test';

test.describe('Executive Dashboard', () => {
  test('should display critical financial KPIs', async ({ page }) => {
    await page.goto('/dashboard/executive');

    // Replace these selectors with your real data-testids
    await expect(page.getByTestId('kpi-total-loans')).toBeVisible();
    await expect(page.getByTestId('chart-revenue')).toBeVisible();

    const totalAmount = await page.getByTestId('kpi-total-loans').innerText();
    expect(totalAmount).toContain('$');
  });
});
