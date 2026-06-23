import { test as base, expect, Page, APIRequestContext } from '@playwright/test';

import { LoginPage } from './pages/LoginPage';
import { USERS } from './data/users';

type AuthenticatedUser = {
  page: Page;
  expectInventoryVisible: () => Promise<void>;
};

type DeniedUser = {
  page: Page;
  expectAccessDenied: () => Promise<void>;
};

type SecurityApi = {
  buildToken: (claims: object) => string;
  getPatientSummary: (token: string) => Promise<ReturnType<APIRequestContext['get']>>;
};

type TestFixtures = {
  standardUser: AuthenticatedUser;
  problemUser: AuthenticatedUser;
  lockedOutUser: DeniedUser;
  securityApi: SecurityApi;
};

async function loginAs(
  page: Page,
  username: string,
  password: string
) {
  const loginPage = new LoginPage(page);

  await loginPage.goto();

  await loginPage.login(username, password);
}

function buildTestJwt(payload: object): string {
  const header = {
    alg: 'HS256',
    typ: 'JWT',
  };

  function encode(section: object): string {
    return Buffer
      .from(JSON.stringify(section))
      .toString('base64url');
  }

  return `${encode(header)}.${encode(payload)}.fake_signature`;
}

export const test = base.extend<TestFixtures>({
  standardUser: async ({ page }, use) => {
    await loginAs(
      page,
      USERS.standard.username,
      USERS.standard.password
    );

    await expect(page).toHaveURL(/inventory/);

    await use({
      page,

      expectInventoryVisible: async () => {
        await expect(
          page.locator('[data-test="inventory-list"]')
        ).toBeVisible();
      },
    });
  },

  problemUser: async ({ page }, use) => {
    await loginAs(
      page,
      USERS.problem.username,
      USERS.problem.password
    );

    await expect(page).toHaveURL(/inventory/);

    await use({
      page,

      expectInventoryVisible: async () => {
        await expect(
          page.locator('[data-test="inventory-list"]')
        ).toBeVisible();
      },
    });
  },

  lockedOutUser: async ({ page }, use) => {
    await loginAs(
      page,
      USERS.lockedOut.username,
      USERS.lockedOut.password
    );

    await use({
      page,

      expectAccessDenied: async () => {
        await expect(
          page.locator('[data-test="error"]')
        ).toContainText('Sorry, this user has been locked out');
      },
    });
  },

  securityApi: async ({ request }, use) => {
    await use({
      buildToken: buildTestJwt,

      getPatientSummary: async (token: string) => {
        return request.get(
          'http://127.0.0.1:8000/secure/patient-summary',
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
      },
    });
  },
});

export { expect };