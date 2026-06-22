import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('standard user can login', async ({ page }) => {

  const loginPage = new LoginPage(page);

  await loginPage.goto();

  await loginPage.login(
    USERS.standard.username,
    USERS.standard.password
  );

  await expect(page).toHaveURL(/inventory/);
});


test('locked out user is denied access', async ({ page }) => {

  const loginPage = new LoginPage(page);

  await loginPage.goto();

  await loginPage.login(
    USERS.lockedOut.username,
    USERS.lockedOut.password
  );

  const errorMessage = page.locator('[data-test="error"]');

  await expect(errorMessage).toBeVisible();

  await expect(errorMessage).toContainText(
    'Sorry, this user has been locked out'
  );
});