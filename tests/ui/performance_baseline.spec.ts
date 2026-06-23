import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('measure login and inventory workflow performance', async ({ page, request }) => {
  const healthStart = Date.now();

  const healthResponse = await request.get(
    'http://127.0.0.1:8000/health'
  );

  const healthDuration = Date.now() - healthStart;

  expect(healthResponse.status()).toBe(200);

  const loginPage = new LoginPage(page);

  const workflowStart = Date.now();

  await loginPage.goto();

  const loginStart = Date.now();

  await loginPage.login(
    USERS.standard.username,
    USERS.standard.password
  );

  await expect(page).toHaveURL(/inventory/);

  const loginDuration = Date.now() - loginStart;

  await expect(
    page.locator('[data-test="inventory-list"]')
  ).toBeVisible();

  const totalWorkflowDuration = Date.now() - workflowStart;

  console.log('');
  console.log('================================');
  console.log('PLAYWRIGHT PERFORMANCE BASELINE');
  console.log('================================');
  console.log(`Health API Duration     : ${healthDuration} ms`);
  console.log(`Login Duration          : ${loginDuration} ms`);
  console.log(`Total Workflow Duration : ${totalWorkflowDuration} ms`);
  console.log('Signal                  : BASELINE_CAPTURED');
  console.log('================================');
  console.log('');

  expect(healthDuration).toBeLessThan(1000);
  expect(loginDuration).toBeLessThan(5000);
  expect(totalWorkflowDuration).toBeLessThan(10000);
});