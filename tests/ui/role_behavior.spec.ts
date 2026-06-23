import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('problem user can login but experiences application issues', async ({ page }) => {

  const loginPage = new LoginPage(page);

  await loginPage.goto();

  await loginPage.login(
    USERS.problem.username,
    USERS.problem.password
  );

  await expect(page).toHaveURL(/inventory/);

  const inventoryItems =
    page.locator('.inventory_item');

  await expect(inventoryItems.first())
    .toBeVisible();
});