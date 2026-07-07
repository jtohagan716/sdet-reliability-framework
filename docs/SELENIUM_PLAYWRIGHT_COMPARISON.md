# Selenium WebDriver and Playwright Comparison

## Purpose

This document compares Selenium WebDriver and Playwright by validating the same synthetic Patient Lookup workflow with both tools.

The SDET Reliability Framework already uses Playwright for browser workflow validation and accessibility-oriented checks. This Selenium WebDriver refresh adds a parallel Selenium example so the same page behavior can be tested and compared across both automation approaches.

The goal is not to replace Playwright in the project. The goal is to maintain practical Selenium WebDriver familiarity and make the differences between Selenium and Playwright easier to understand.

---

## Compared Test Files

| Tool | Test File |
|---|---|
| Playwright | `tests/ui/patient_lookup_accessibility.spec.ts` |
| Selenium WebDriver | `tests/selenium/test_patient_lookup_selenium.py` |

---

## Page Under Test

Both suites validate the same browser-facing page:

```text
/patient-lookup
```

The page provides a synthetic patient lookup form with:

- page title
- heading
- instructional text
- patient ID input
- submit button
- live result region
- client-side validation feedback
- API-backed lookup behavior

The page uses synthetic data only.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

---

## Shared Validation Scenarios

Both the Playwright and Selenium suites validate the same core workflow behavior.

| Scenario | Playwright | Selenium WebDriver |
|---|---:|---:|
| Page title is `Patient Lookup` | yes | yes |
| Main heading is visible | yes | yes |
| Instructional text is visible | yes | yes |
| Patient ID input is available | yes | yes |
| Lookup button is available | yes | yes |
| Result region starts with default text | yes | yes |
| Patient ID input is keyboard reachable | yes | yes |
| Lookup button is keyboard reachable | yes | yes |
| Empty submission shows validation feedback | yes | yes |
| Patient `1001` lookup succeeds | yes | yes |
| Patient `9999` lookup returns expected 404 message | yes | yes |

---

## Playwright Validation Style

The Playwright suite uses user-facing locators that align closely with how a user or assistive technology would understand the page.

Examples:

```typescript
page.getByRole('heading', { name: 'Patient Lookup' })
page.getByLabel('Patient ID')
page.getByRole('button', { name: 'Lookup Patient' })
page.getByRole('region', { name: 'Lookup result' })
```

This style encourages tests that are readable and tied to accessible page structure.

For example, this Playwright assertion validates the result region by accessible role and name:

```typescript
await expect(
    page.getByRole('region', { name: 'Lookup result' })
).toContainText('Patient lookup succeeded for 1001.');
```

---

## Selenium WebDriver Validation Style

The Selenium suite uses lower-level Document Object Model (DOM) locators such as ID, CSS selector, tag name, and XPath.

Examples:

```python
driver.find_element(By.ID, "patient-id")
driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
driver.find_element(By.ID, "lookup-result")
driver.find_element(By.XPATH, "//button[normalize-space()='Lookup Patient']")
```

This style is flexible and widely used, but it often requires more explicit knowledge of the page structure.

For example, this Selenium assertion waits for text to appear in the result region by ID:

```python
wait.until(
    EC.text_to_be_present_in_element(
        (By.ID, "lookup-result"),
        "Patient lookup succeeded for 1001.",
    )
)
```

---

## Locator Comparison

| Validation Need | Playwright Locator | Selenium Locator |
|---|---|---|
| Main heading | `page.getByRole('heading', { name: 'Patient Lookup' })` | `driver.find_element(By.TAG_NAME, "h1")` |
| Patient ID input | `page.getByLabel('Patient ID')` | `driver.find_element(By.ID, "patient-id")` |
| Submit button | `page.getByRole('button', { name: 'Lookup Patient' })` | `driver.find_element(By.CSS_SELECTOR, "button[type='submit']")` |
| Result region | `page.getByRole('region', { name: 'Lookup result' })` | `driver.find_element(By.ID, "lookup-result")` |
| Button text by visible name | role locator | XPath with normalized text |

---

## Wait Strategy Comparison

### Playwright

Playwright includes built-in auto-waiting behavior for many actions and assertions.

Example:

```typescript
await page.getByLabel('Patient ID').fill('1001');
await page.getByRole('button', { name: 'Lookup Patient' }).click();

await expect(
    page.getByRole('region', { name: 'Lookup result' })
).toContainText('Patient lookup succeeded for 1001.');
```

The test is concise because Playwright automatically waits for many page conditions.

### Selenium WebDriver

Selenium commonly requires explicit waits.

Example:

```python
patient_id_input = wait.until(
    EC.visibility_of_element_located((By.ID, "patient-id"))
)

lookup_button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
)

patient_id_input.send_keys("1001")
lookup_button.click()

wait.until(
    EC.text_to_be_present_in_element(
        (By.ID, "lookup-result"),
        "Patient lookup succeeded for 1001.",
    )
)
```

The Selenium version is more verbose, but it makes the wait strategy very explicit.

---

## Keyboard Testing Comparison

Both suites validate that the input and submit button are reachable by keyboard.

### Playwright

```typescript
await page.keyboard.press('Tab');
await expect(patientIdInput).toBeFocused();

await page.keyboard.press('Tab');
await expect(lookupButton).toBeFocused();
```

### Selenium WebDriver

```python
body = driver.find_element(By.TAG_NAME, "body")

body.send_keys(Keys.TAB)

wait.until(
    lambda current_driver: (
        current_driver.switch_to.active_element.get_attribute("id")
        == "patient-id"
    )
)

active_element = driver.switch_to.active_element
assert active_element.get_attribute("id") == "patient-id"

active_element.send_keys(Keys.TAB)

wait.until(
    lambda current_driver: (
        current_driver.switch_to.active_element.tag_name.lower() == "button"
    )
)
```

Selenium keyboard validation is more manual because the test directly inspects the active browser element.

---

## Fixture and Browser Lifecycle Comparison

### Playwright

Playwright test fixtures provide the `page` object automatically.

Example:

```typescript
test('successful patient lookup updates the live result region', async ({ page }) => {
    await page.goto(`${BASE_URL}/patient-lookup`);
});
```

The browser/page lifecycle is handled by Playwright's test runner.

### Selenium WebDriver

The Selenium suite creates and closes the browser through a Pytest fixture.

Example:

```python
@pytest.fixture
def driver():
    options = EdgeOptions()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1200,800")

    browser = webdriver.Edge(options=options)

    try:
        yield browser
    finally:
        browser.quit()
```

This makes browser lifecycle management more explicit.

---

## Headless Execution

The Selenium suite supports headless execution by default.

```python
HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() != "false"
```

Default behavior:

```text
headless mode enabled
```

To run with the browser visible:

```powershell
$env:SELENIUM_HEADLESS="false"
python -m pytest -q .\tests\selenium\test_patient_lookup_selenium.py
Remove-Item Env:\SELENIUM_HEADLESS
```

This is useful when learning or debugging browser behavior.

---

## Run Commands

Start the Docker Compose stack:

```powershell
docker compose up -d --build
```

Confirm API health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Run the Playwright suite:

```powershell
npx playwright test tests/ui/patient_lookup_accessibility.spec.ts --project=chromium
```

Run the Selenium suite:

```powershell
python -m pytest -q .\tests\selenium\test_patient_lookup_selenium.py
```

---

## Expected Results

Expected Playwright result:

```text
5 passed
```

Expected Selenium result:

```text
5 passed
```

The exact runtime may differ.

Selenium can be slower on first run because Selenium Manager may need to resolve browser driver support.

---

## Practical Differences Observed

| Area | Playwright | Selenium WebDriver |
|---|---|---|
| Locator style | user-facing roles and labels | DOM-level IDs, CSS, XPath, tags |
| Wait behavior | built-in auto-waiting | explicit waits commonly required |
| Test readability | concise and user-centered | more verbose and implementation-aware |
| Browser lifecycle | handled by Playwright runner | explicitly managed through WebDriver |
| Keyboard testing | direct keyboard API | active element inspection |
| Accessibility alignment | strong role/label locator support | possible, but more manual |
| Industry usage | modern and growing | long-established and widely requested |
| Learning value | concise workflow automation | strong fundamentals for browser automation |

---

## Why Both Are Useful

Playwright is strong for modern browser automation because it is concise, fast, and encourages accessible user-facing locators.

Selenium WebDriver remains important because it is widely used in many QA and SDET job descriptions, especially in established enterprise environments.

Using both tools against the same page helps reinforce the core automation concepts that transfer between frameworks:

- browser navigation
- element location
- form interaction
- button actions
- keyboard interaction
- explicit waiting
- assertions
- workflow validation
- cleanup
- repeatable regression testing

---

## Project Positioning

The main browser automation layer for this project remains Playwright.

The Selenium suite is an optional learning and comparison layer.

It demonstrates Selenium WebDriver fundamentals against the same synthetic Patient Lookup workflow already validated by Playwright.

This keeps the project focused while also supporting practical Selenium skill development.

---

## Interview Talking Point

A concise way to describe this work:

```text
My main project uses Playwright for browser automation, accessibility smoke validation, and UI workflow checks. I added a parallel Selenium WebDriver suite against the same patient lookup workflow so I could compare Playwright role-based locators and auto-waiting with Selenium DOM locators, explicit waits, keyboard handling, and WebDriver lifecycle management.
```

A slightly shorter version:

```text
I built matching Playwright and Selenium tests against the same workflow to compare the tools directly. The exercise reinforced common automation concepts like locators, waits, form actions, assertions, keyboard behavior, and browser cleanup.
```

---

## Scope

This Selenium work is intentionally limited.

It is not intended to replace the Playwright suite, become a full Selenium framework, or expand the project beyond its main reliability-validation purpose.

The purpose is to provide a complete, working Selenium comparison example that supports practical learning and job-readiness.
