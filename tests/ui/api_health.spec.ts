import { test, expect } from '@playwright/test';

test('Synthetic Canary - Local API Health Check', async ({ request }) => {
    const start = Date.now();

    const response = await request.get(
        'http://127.0.0.1:8000/health'
    );

    console.log('');
    console.log('================================');
    console.log('API RESPONSE TRACE');
    console.log('================================');
    console.log(`HTTP Status : ${response.status()}`);
    console.log(`Status Text : ${response.statusText()}`);

    const payload = await response.json();

    console.log('Payload:');
    console.log(JSON.stringify(payload, null, 2));
    console.log('================================');
    console.log('');

    expect(response.ok()).toBeTruthy();
    expect(payload.status).toBe('UP');

    const elapsed = Date.now() - start;

    expect(elapsed).toBeLessThan(1000);

    console.log('');
    console.log('================================');
    console.log('API HEALTH CANARY');
    console.log('================================');
    console.log('Journey : Local API Health Check');
    console.log('Status  : PASS');
    console.log(`Duration: ${elapsed} ms`);
    console.log('Signal  : HEALTHY');
    console.log('================================');
    console.log('');
});