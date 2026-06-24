import { test, expect } from '@playwright/test';

test('metrics endpoint exposes reliability signals', async ({ request }) => {
  const response = await request.get('http://127.0.0.1:8000/metrics');

  expect(response.ok()).toBeTruthy();

  const body = await response.text();

  expect(body).toContain('sdet_api_request_count_total');
  expect(body).toContain('sdet_api_request_latency_seconds');
});

test('health endpoint reports service availability', async ({ request }) => {
  const response = await request.get('http://127.0.0.1:8000/health');

  expect(response.status()).toBe(200);

  const body = await response.json();

  expect(body.status).toBe('UP');
});