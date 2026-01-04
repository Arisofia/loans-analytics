import { test, expect } from '@playwright/test';

test.describe('Dashboard Smoke Tests', () => {
  test('Executive Overview (Board) Dashboard', async ({ page }) => {
    await page.goto('/board');
    await expect(page.getByRole('heading', { name: 'Board Dashboard' })).toBeVisible();
    await expect(page.getByText('Annual Recurring Revenue (ARR)')).toBeVisible();
    await expect(page.getByText('Origination Volume')).toBeVisible();
    await expect(page.getByText('Portfolio at Risk 90 (PAR90)')).toBeVisible();
  });

  test('Portfolio Analytics Dashboard', async ({ page }) => {
    await page.goto('/analytics');
    await expect(page.getByRole('heading', { name: 'Portfolio performance dashboard' })).toBeVisible();
    // Wait for the dashboard component to render
    await expect(page.getByText('Portfolio health')).toBeVisible();
    await expect(page.getByText('Delinquency rate')).toBeVisible();
    await expect(page.getByText('Portfolio yield')).toBeVisible();
  });

  test('Financial Performance (CFO) Dashboard', async ({ page }) => {
    await page.goto('/cfo');
    await expect(page.getByRole('heading', { name: 'CFO Dashboard' })).toBeVisible();
    await expect(page.getByText('Cash Position')).toBeVisible();
    await expect(page.getByText('Collection Rate')).toBeVisible();
    await expect(page.getByText('Write-off Rate')).toBeVisible();
  });

  test('Operational Status (Risk) Dashboard', async ({ page }) => {
    await page.goto('/risk');
    await expect(page.getByRole('heading', { name: 'Risk Dashboard' })).toBeVisible();
    await expect(page.getByText('Portfolio at Risk 90 (PAR90)')).toBeVisible();
    await expect(page.getByText('Roll-rate to Default (90d)')).toBeVisible();
    await expect(page.getByText('Collections Efficiency')).toBeVisible();
  });

  test('Strategic OKRs (Growth) Dashboard', async ({ page }) => {
    await page.goto('/growth');
    await expect(page.getByRole('heading', { name: 'Growth Dashboard' })).toBeVisible();
    await expect(page.getByText('Origination Volume')).toBeVisible();
    await expect(page.getByText('Client Retention')).toBeVisible();
    await expect(page.getByText('Channel CAC-to-LTV')).toBeVisible();
  });
});
