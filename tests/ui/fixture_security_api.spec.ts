import { test, expect } from './fixtures';

test('securityApi fixture allows provider access to patient summary', async ({ securityApi }) => {
  const token = securityApi.buildToken({
    sub: 'james',
    role: 'provider',
    iss: 'https://company-login.com',
    exp: 1890000000,
  });

  const response = await securityApi.getPatientSummary(token);

  expect(response.status()).toBe(200);

  const payload = await response.json();

  expect(payload.status).toBe('ACCESS_GRANTED');
  expect(payload.resource).toBe('patient-summary');
  expect(payload.subject).toBe('james');
  expect(payload.role).toBe('provider');
});


test('securityApi fixture rejects wrong role for patient summary', async ({ securityApi }) => {
  const token = securityApi.buildToken({
    sub: 'james',
    role: 'admin',
    iss: 'https://company-login.com',
    exp: 1890000000,
  });

  const response = await securityApi.getPatientSummary(token);

  expect(response.status()).toBe(403);

  const payload = await response.json();

  expect(payload.detail).toBe('ROLE_NOT_AUTHORIZED');
});