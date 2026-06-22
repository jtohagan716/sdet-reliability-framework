import { test, expect } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

test('standard user is authorized to access inventory page', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    await loginPage.login(
        USERS.standard.username,
        USERS.standard.password
    );

    await expect(page).toHaveURL(/inventory/);

    await expect(page.locator('[data-test="inventory-list"]')).toBeVisible();
});


test('locked out user is not authorized to access inventory page', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    await loginPage.login(
        USERS.lockedOut.username,
        USERS.lockedOut.password
    );

    await expect(page).not.toHaveURL(/inventory/);

    await expect(page.locator('[data-test="error"]')).toContainText(
        'Sorry, this user has been locked out'
    );
});