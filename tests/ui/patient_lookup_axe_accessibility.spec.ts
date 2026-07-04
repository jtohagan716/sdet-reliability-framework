import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Patient Lookup axe accessibility scan', () => {
  test('patient lookup page has no automatically detectable accessibility violations', async ({ page }) => {
    test.setTimeout(60000);

    await page.goto('http://127.0.0.1:8000/patient-lookup');
    await expect(page.getByRole('heading', { name: 'Patient Lookup' })).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
