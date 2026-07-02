import { test, expect } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:8000';

test.describe('patient lookup accessibility smoke validation', () => {
    test('page exposes basic accessible structure', async ({ page }) => {
        await page.goto(`${BASE_URL}/patient-lookup`);

        await expect(page).toHaveTitle('Patient Lookup');

        await expect(
            page.getByRole('heading', { name: 'Patient Lookup' })
        ).toBeVisible();

        await expect(page.getByText('Enter a synthetic patient ID')).toBeVisible();

        await expect(page.getByLabel('Patient ID')).toBeVisible();

        await expect(
            page.getByRole('button', { name: 'Lookup Patient' })
        ).toBeVisible();

        await expect(
            page.getByRole('region', { name: 'Lookup result' })
        ).toContainText('No lookup has been submitted.');
    });

    test('patient ID input and submit button are keyboard reachable', async ({ page }) => {
        await page.goto(`${BASE_URL}/patient-lookup`);

        const patientIdInput = page.getByLabel('Patient ID');
        const lookupButton = page.getByRole('button', { name: 'Lookup Patient' });

        await page.keyboard.press('Tab');
        await expect(patientIdInput).toBeFocused();

        await page.keyboard.press('Tab');
        await expect(lookupButton).toBeFocused();
    });

    test('empty submission displays accessible validation feedback', async ({ page }) => {
        await page.goto(`${BASE_URL}/patient-lookup`);

        await page.getByRole('button', { name: 'Lookup Patient' }).click();

        await expect(
            page.getByRole('region', { name: 'Lookup result' })
        ).toContainText('Enter a patient ID before submitting.');
    });

    test('successful patient lookup updates the live result region', async ({ page }) => {
        await page.goto(`${BASE_URL}/patient-lookup`);

        await page.getByLabel('Patient ID').fill('1001');
        await page.getByRole('button', { name: 'Lookup Patient' }).click();

        await expect(
            page.getByRole('region', { name: 'Lookup result' })
        ).toContainText('Patient lookup succeeded for 1001.');
    });

    test('not-found patient lookup reports the expected status', async ({ page }) => {
        await page.goto(`${BASE_URL}/patient-lookup`);

        await page.getByLabel('Patient ID').fill('9999');
        await page.getByRole('button', { name: 'Lookup Patient' }).click();

        await expect(
            page.getByRole('region', { name: 'Lookup result' })
        ).toContainText('Patient lookup returned status 404.');
    });
});