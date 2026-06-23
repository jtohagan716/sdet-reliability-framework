import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('API health check supports successful UI login workflow', async ({ page, request }) => {
  const healthResponse = await request.get(
    'http://127.0.0.1:8000/health'
  );

  expect(healthResponse.status()).toBe(200);

  const healthPayload = await healthResponse.json();

  expect(healthPayload.status).toBe('UP');

  const loginPage = new LoginPage(page);

  await loginPage.goto();

  await loginPage.login(
    USERS.standard.username,
    USERS.standard.password
  );

  await expect(page).toHaveURL(/inventory/);

  await expect(
    page.locator('[data-test="inventory-list"]')
  ).toBeVisible();
});