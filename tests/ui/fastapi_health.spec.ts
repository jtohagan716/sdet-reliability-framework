import { test, expect } from '@playwright/test';

test('FastAPI health endpoint returns UP status', async ({ request }) => {
  const response = await request.get('http://127.0.0.1:8000/health');

  expect(response.status()).toBe(200);

  const payload = await response.json();

  expect(payload.status).toBe('UP');
  expect(payload.timestamp_utc).toBeTruthy();

  console.log('');
  console.log('================================');
  console.log('FASTAPI HEALTH VIA PLAYWRIGHT');
  console.log('================================');
  console.log(`HTTP Status : ${response.status()}`);
  console.log(`Service     : ${payload.status}`);
  console.log(`Timestamp   : ${payload.timestamp_utc}`);
  console.log('================================');
  console.log('');
});