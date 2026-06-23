import { test, expect } from '@playwright/test';

test('simulate backend failure with mocked response', async ({ page }) => {
  await page.route('**/inventory.html', async route => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        error: 'SIMULATED_BACKEND_FAILURE',
      }),
    });
  });

  await page.goto('https://www.saucedemo.com/inventory.html');

  const content = await page.content();

  console.log('');
  console.log('================================');
  console.log('MOCKED FAILURE TEST');
  console.log('================================');
  console.log('Backend Response : 500');
  console.log('Signal           : MOCK ACTIVE');
  console.log('================================');
  console.log('');

  expect(content).toContain('SIMULATED_BACKEND_FAILURE');
});