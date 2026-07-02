import { test, expect } from '@playwright/test';

test('metrics endpoint exposes expanded reliability and performance signals', async ({ request }) => {
  const healthResponse = await request.get('http://127.0.0.1:8000/health');
  expect(healthResponse.status()).toBe(200);

  const patientSuccessResponse = await request.get('http://127.0.0.1:8000/patients/1001');
  expect(patientSuccessResponse.status()).toBe(200);

  const patientNotFoundResponse = await request.get('http://127.0.0.1:8000/patients/9999');
  expect(patientNotFoundResponse.status()).toBe(404);

  const metricsResponse = await request.get('http://127.0.0.1:8000/metrics');
  expect(metricsResponse.status()).toBe(200);

  const body = await metricsResponse.text();

  expect(body).toContain('sdet_http_requests_total');
  expect(body).toContain('sdet_http_request_duration_seconds');
  expect(body).toContain('sdet_patient_lookup_total');

  expect(body).toContain('path="/patients/{patient_id}"');
  expect(body).not.toContain('path="/patients/1001"');
  expect(body).not.toContain('path="/patients/9999"');

  expect(body).toContain('outcome="success"');
  expect(body).toContain('outcome="not_found"');
});

test('health endpoint reports service availability', async ({ request }) => {
  const response = await request.get('http://127.0.0.1:8000/health');

  expect(response.status()).toBe(200);

  const body = await response.json();

  expect(body.status).toBe('UP');
});