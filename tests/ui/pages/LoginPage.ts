import { Page } from '@playwright/test';

export class LoginPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('https://www.saucedemo.com');
  }

  async login(
    username: string,
    password: string
  ) {
    await this.page.locator('[data-test="username"]').fill(username);

    await this.page.locator('[data-test="password"]').fill(password);

    await this.page.locator('[data-test="login-button"]').click();
  }
}