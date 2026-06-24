import { test, expect } from '@playwright/test';

test('prometheus can scrape application metrics', async ({ request }) => {
  const response = await request.get(
    'http://127.0.0.1:9090/api/v1/query?query=up{job="sdet-reliability-api"}'
  );

  expect(response.ok()).toBeTruthy();

  const body = await response.json();

  expect(body.status).toBe('success');

  const value = body.data.result[0].value[1];

  expect(value).toBe('1');
});