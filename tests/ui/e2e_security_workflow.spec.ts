import { test, expect } from '@playwright/test';

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

test('end-to-end security workflow grants access to valid provider token', async ({ request }) => {
  const token = buildTestJwt({
    sub: 'james',
    role: 'provider',
    iss: 'https://company-login.com',
    exp: 1890000000,
  });

  const response = await request.get(
    'http://127.0.0.1:8000/secure/patient-summary',
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  expect(response.status()).toBe(200);

  const payload = await response.json();

  expect(payload.status).toBe('ACCESS_GRANTED');
  expect(payload.resource).toBe('patient-summary');
  expect(payload.subject).toBe('james');
  expect(payload.role).toBe('provider');

  console.log('');
  console.log('================================');
  console.log('E2E SECURITY WORKFLOW');
  console.log('================================');
  console.log(`Subject  : ${payload.subject}`);
  console.log(`Role     : ${payload.role}`);
  console.log(`Resource : ${payload.resource}`);
  console.log(`Status   : ${payload.status}`);
  console.log('Signal   : ACCESS GRANTED');
  console.log('================================');
  console.log('');
});


test('end-to-end security workflow denies valid token with wrong role', async ({ request }) => {
  const token = buildTestJwt({
    sub: 'james',
    role: 'admin',
    iss: 'https://company-login.com',
    exp: 1890000000,
  });

  const response = await request.get(
    'http://127.0.0.1:8000/secure/patient-summary',
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  expect(response.status()).toBe(403);

  const payload = await response.json();

  expect(payload.detail).toBe('ROLE_NOT_AUTHORIZED');
});