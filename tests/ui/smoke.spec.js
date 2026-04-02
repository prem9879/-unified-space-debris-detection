const { test, expect } = require('@playwright/test');

test('home page renders critical controls', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#heroLoadAllBtn')).toBeVisible();
  await expect(page.locator('#heroExplorerBtn')).toBeVisible();
  await expect(page.locator('#predictForm')).toBeVisible();
  await expect(page.locator('#runDemoBtn')).toBeVisible();
  await expect(page.locator('#securityModeChip')).toBeVisible();
});

test('health endpoint is reachable from browser context', async ({ request }) => {
  const res = await request.get('/healthz');
  expect(res.ok()).toBeTruthy();
  const payload = await res.json();
  expect(payload.status).toBe('ok');
});
