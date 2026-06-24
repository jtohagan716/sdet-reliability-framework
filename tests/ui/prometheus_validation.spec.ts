import { test, expect } from '@playwright/test';

test('prometheus can scrape application metrics', async ({ request }) => {
  await expect
    .poll(
      async () => {
        const response = await request.get(
          'http://127.0.0.1:9090/api/v1/query?query=up{job="sdet-reliability-api"}'
        );

        if (!response.ok()) {
          return 'NOT_READY';
        }

        const body = await response.json();
        return body.data?.result?.[0]?.value?.[1] ?? 'NO_DATA';
      },
      {
        timeout: 30000,
        intervals: [1000, 2000, 3000, 5000],
      }
    )
    .toBe('1');
});