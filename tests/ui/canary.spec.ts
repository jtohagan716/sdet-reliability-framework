import { test, expect } from '@playwright/test';

test('Synthetic Canary - Framework Health Check', async ({ page }) => {

    const start = Date.now();

    await page.goto('https://example.com');

    await expect(page).toHaveTitle(/Example Domain/);

    const elapsed = Date.now() - start;

    console.log('');
    console.log('================================');
    console.log('SYNTHETIC CANARY');
    console.log('================================');
    console.log(`Journey : Framework Health Check`);
    console.log(`Status  : PASS`);
    console.log(`Duration: ${elapsed} ms`);
    console.log(`Signal  : HEALTHY`);
    console.log('================================');
    console.log('');
});