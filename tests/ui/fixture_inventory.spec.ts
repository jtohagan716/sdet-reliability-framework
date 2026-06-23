import { test, expect } from './fixtures';

test('standard user fixture provides authenticated inventory access', async ({ standardUser }) => {
  await standardUser.expectInventoryVisible();

  await expect(standardUser.page).toHaveURL(/inventory/);
});