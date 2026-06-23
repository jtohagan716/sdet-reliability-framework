import { test, expect } from './fixtures';

test('standard user fixture provides inventory access', async ({ standardUser }) => {
  await standardUser.expectInventoryVisible();

  await expect(standardUser.page).toHaveURL(/inventory/);
});

test('problem user fixture provides inventory access with known user behavior', async ({ problemUser }) => {
  await problemUser.expectInventoryVisible();

  await expect(problemUser.page).toHaveURL(/inventory/);
});

test('locked out user fixture verifies access denial', async ({ lockedOutUser }) => {
  await lockedOutUser.expectAccessDenied();

  await expect(lockedOutUser.page).not.toHaveURL(/inventory/);
});