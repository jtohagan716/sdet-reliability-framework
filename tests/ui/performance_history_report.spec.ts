import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

type PerformanceRecord = {
  timestampUtc: string;
  healthApiMs: number;
  loginMs: number;
  totalWorkflowMs: number;
  signal: string;
};

function calculateVariancePercent(
  current: number,
  previous: number
): number {
  if (previous === 0) {
    return 0;
  }

  return Number((((current - previous) / previous) * 100).toFixed(2));
}

function classifyVariance(variancePercent: number): string {
  if (variancePercent <= -10) {
    return 'IMPROVING';
  }

  if (variancePercent >= 25) {
    return 'DEGRADING';
  }

  return 'STABLE';
}

test('generate Playwright performance history report', async () => {
  const historyFile = path.join(
    process.cwd(),
    'reports',
    'baselines',
    'playwright_performance_history.json'
  );

  expect(fs.existsSync(historyFile)).toBeTruthy();

  const history = JSON.parse(
    fs.readFileSync(historyFile, 'utf-8')
  ) as PerformanceRecord[];

  expect(history.length).toBeGreaterThanOrEqual(2);

  const previous = history[history.length - 2];
  const current = history[history.length - 1];

  const healthVariance =
    calculateVariancePercent(current.healthApiMs, previous.healthApiMs);

  const loginVariance =
    calculateVariancePercent(current.loginMs, previous.loginMs);

  const workflowVariance =
    calculateVariancePercent(current.totalWorkflowMs, previous.totalWorkflowMs);

  const healthSignal = classifyVariance(healthVariance);
  const loginSignal = classifyVariance(loginVariance);
  const workflowSignal = classifyVariance(workflowVariance);

  console.log('');
  console.log('================================');
  console.log('PLAYWRIGHT PERFORMANCE HISTORY REPORT');
  console.log('================================');

  console.log(`Previous Run : ${previous.timestampUtc}`);
  console.log(`Current Run  : ${current.timestampUtc}`);
  console.log('');

  console.log('Health API');
  console.log(`Previous : ${previous.healthApiMs} ms`);
  console.log(`Current  : ${current.healthApiMs} ms`);
  console.log(`Variance : ${healthVariance}%`);
  console.log(`Signal   : ${healthSignal}`);
  console.log('');

  console.log('Login');
  console.log(`Previous : ${previous.loginMs} ms`);
  console.log(`Current  : ${current.loginMs} ms`);
  console.log(`Variance : ${loginVariance}%`);
  console.log(`Signal   : ${loginSignal}`);
  console.log('');

  console.log('Total Workflow');
  console.log(`Previous : ${previous.totalWorkflowMs} ms`);
  console.log(`Current  : ${current.totalWorkflowMs} ms`);
  console.log(`Variance : ${workflowVariance}%`);
  console.log(`Signal   : ${workflowSignal}`);

  console.log('================================');
  console.log('');

  expect(history.length).toBeGreaterThanOrEqual(2);
});