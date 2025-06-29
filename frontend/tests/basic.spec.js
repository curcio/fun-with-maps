import { test, expect } from '@playwright/test';

// Basic smoke test to ensure app loads

test('index page has header', async ({ page, baseURL }) => {
  await page.goto(baseURL);
  await expect(page.locator('h1')).toHaveText(/guess the country/i);
});
