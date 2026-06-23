import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('standard user login captures network responses during inventory load', async ({ page }) => {
  const observedResponses: string[] = [];

  page.on('response', response => {
    observedResponses.push(
      `${response.status()} ${response.url()}`
    );
  });

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

  console.log('');
  console.log('================================');
  console.log('NETWORK INSPECTION');
  console.log('================================');

  for (const response of observedResponses.slice(0, 10)) {
    console.log(response);
  }

  console.log('================================');
  console.log('');

  expect(
    observedResponses.some(response =>
      response.includes('200')
    )
  ).toBeTruthy();
});