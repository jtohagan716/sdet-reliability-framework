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

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 0) {
    return Number(((sorted[middle - 1] + sorted[middle]) / 2).toFixed(2));
  }

  return sorted[middle];
}

function variancePercent(current: number, baseline: number): number {
  if (baseline === 0) {
    return 0;
  }

  return Number((((current - baseline) / baseline) * 100).toFixed(2));
}

function classifyAgainstMedian(variance: number): string {
  if (variance <= 15) {
    return 'STABLE';
  }

  if (variance <= 50) {
    return 'ELEVATED';
  }

  return 'DEGRADED';
}

test('generate Playwright performance trend report using median baseline', async () => {
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

  expect(history.length).toBeGreaterThanOrEqual(3);

  const latest = history[history.length - 1];
  const previousRuns = history.slice(0, history.length - 1);

  const healthMedian = median(
    previousRuns.map(record => record.healthApiMs)
  );

  const loginMedian = median(
    previousRuns.map(record => record.loginMs)
  );

  const workflowMedian = median(
    previousRuns.map(record => record.totalWorkflowMs)
  );

  const healthVariance = variancePercent(
    latest.healthApiMs,
    healthMedian
  );

  const loginVariance = variancePercent(
    latest.loginMs,
    loginMedian
  );

  const workflowVariance = variancePercent(
    latest.totalWorkflowMs,
    workflowMedian
  );

  const healthSignal = classifyAgainstMedian(healthVariance);
  const loginSignal = classifyAgainstMedian(loginVariance);
  const workflowSignal = classifyAgainstMedian(workflowVariance);

  console.log('');
  console.log('================================');
  console.log('PLAYWRIGHT PERFORMANCE TREND REPORT');
  console.log('================================');
  console.log(`Baseline Method      : MEDIAN`);
  console.log(`Historical Runs Used : ${previousRuns.length}`);
  console.log(`Latest Run           : ${latest.timestampUtc}`);
  console.log('');

  console.log('Health API');
  console.log(`Historical Median : ${healthMedian} ms`);
  console.log(`Latest            : ${latest.healthApiMs} ms`);
  console.log(`Variance          : ${healthVariance}%`);
  console.log(`Signal            : ${healthSignal}`);
  console.log('');

  console.log('Login');
  console.log(`Historical Median : ${loginMedian} ms`);
  console.log(`Latest            : ${latest.loginMs} ms`);
  console.log(`Variance          : ${loginVariance}%`);
  console.log(`Signal            : ${loginSignal}`);
  console.log('');

  console.log('Total Workflow');
  console.log(`Historical Median : ${workflowMedian} ms`);
  console.log(`Latest            : ${latest.totalWorkflowMs} ms`);
  console.log(`Variance          : ${workflowVariance}%`);
  console.log(`Signal            : ${workflowSignal}`);

  console.log('================================');
  console.log('');

  expect(history.length).toBeGreaterThanOrEqual(3);
});