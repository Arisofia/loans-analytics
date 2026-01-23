import { test, expect } from '@playwright/test';

test('Portfolio dashboard smoke', async ({ page }) => {
  await page.goto('/dashboard/portfolio', { waitUntil: 'networkidle' });
  await expect(page.getByTestId('dashboard-portfolio')).toBeVisible();
});
