import { expect, test } from '@playwright/test'

test('web app responds and renders', async ({ page }) => {
  const resp = await page.goto('/')
  expect(resp?.ok()).toBeTruthy()
  await expect(page.locator('html')).toBeVisible()
})

test('page has title or content', async ({ page }) => {
  await page.goto('/')
  const title = await page.title()
  const html = await page.locator('html').innerHTML()
  expect(title.length > 0 || html.length > 0).toBeTruthy()
})
