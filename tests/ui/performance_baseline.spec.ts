import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

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

  const report = {
    timestampUtc: new Date().toISOString(),
    healthApiMs: healthDuration,
    loginMs: loginDuration,
    totalWorkflowMs: totalWorkflowDuration,
    signal: 'BASELINE_CAPTURED',
  };

  const outputDirectory = path.join(
    process.cwd(),
    'reports',
    'baselines'
  );

  const outputFile = path.join(
    outputDirectory,
    'playwright_performance_history.json'
  );

  if (!fs.existsSync(outputDirectory)) {
    fs.mkdirSync(outputDirectory, { recursive: true });
  }

  let history: object[] = [];

  if (fs.existsSync(outputFile)) {
    const existingContent = fs.readFileSync(outputFile, 'utf-8');

    if (existingContent.trim().length > 0) {
      history = JSON.parse(existingContent);
    }
  }

  history.push(report);

  fs.writeFileSync(
    outputFile,
    JSON.stringify(history, null, 2)
  );

  console.log('');
  console.log('================================');
  console.log('PLAYWRIGHT PERFORMANCE BASELINE');
  console.log('================================');
  console.log(`Health API Duration     : ${healthDuration} ms`);
  console.log(`Login Duration          : ${loginDuration} ms`);
  console.log(`Total Workflow Duration : ${totalWorkflowDuration} ms`);
  console.log(`History File            : ${outputFile}`);
  console.log('Signal                  : BASELINE_CAPTURED');
  console.log('================================');
  console.log('');

  expect(healthDuration).toBeLessThan(1000);
  expect(loginDuration).toBeLessThan(5000);
  expect(totalWorkflowDuration).toBeLessThan(10000);
});