"""
Selenium WebDriver smoke validation for the synthetic Patient Lookup page.

This test module intentionally parallels the existing Playwright accessibility
smoke validation in:

    tests/ui/patient_lookup_accessibility.spec.ts

The goal is to compare the same browser workflow across Playwright and
Selenium WebDriver.

Playwright emphasizes role-based and label-based locators.
Selenium emphasizes lower-level DOM locators, explicit waits, keyboard actions,
and direct element inspection.

Selenium is intentionally optional. If Selenium is not installed, this module
is skipped during the default Pytest run. To run these tests locally, install:

    python -m pip install -r requirements-selenium.txt
"""

import os

import pytest

pytest.importorskip(
    "selenium",
    reason="Selenium is optional. Install requirements-selenium.txt to run Selenium comparison tests.",
)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() != "false"


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


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)


def open_patient_lookup(driver, wait):
    driver.get(f"{BASE_URL}/patient-lookup")
    wait.until(lambda current_driver: current_driver.title == "Patient Lookup")


def lookup_patient(driver, wait, patient_id):
    patient_id_input = wait.until(
        EC.visibility_of_element_located((By.ID, "patient-id"))
    )

    lookup_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )

    patient_id_input.clear()
    patient_id_input.send_keys(patient_id)
    lookup_button.click()


def result_region(driver):
    return driver.find_element(By.ID, "lookup-result")


def test_page_exposes_basic_accessible_structure(driver, wait):
    """
    Parallel to Playwright:

    page exposes basic accessible structure
    """

    open_patient_lookup(driver, wait)

    assert driver.title == "Patient Lookup"

    heading = wait.until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert heading.text == "Patient Lookup"

    instructions = driver.find_element(By.ID, "lookup-instructions")
    assert "Enter a synthetic patient ID" in instructions.text

    label = driver.find_element(By.CSS_SELECTOR, "label[for='patient-id']")
    assert label.text == "Patient ID"

    patient_id_input = driver.find_element(By.ID, "patient-id")
    assert patient_id_input.is_displayed()
    assert patient_id_input.get_attribute("name") == "patient-id"
    assert patient_id_input.get_attribute("autocomplete") == "off"

    lookup_button = driver.find_element(
        By.XPATH,
        "//button[normalize-space()='Lookup Patient']",
    )
    assert lookup_button.is_displayed()
    assert lookup_button.get_attribute("type") == "submit"

    lookup_result = result_region(driver)
    assert lookup_result.is_displayed()
    assert lookup_result.get_attribute("aria-label") == "Lookup result"
    assert lookup_result.get_attribute("aria-live") == "polite"
    assert "No lookup has been submitted." in lookup_result.text


def test_patient_id_input_and_submit_button_are_keyboard_reachable(driver, wait):
    """
    Parallel to Playwright:

    patient ID input and submit button are keyboard reachable
    """

    open_patient_lookup(driver, wait)

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

    active_element = driver.switch_to.active_element
    assert active_element.text == "Lookup Patient"


def test_empty_submission_displays_accessible_validation_feedback(driver, wait):
    """
    Parallel to Playwright:

    empty submission displays accessible validation feedback
    """

    open_patient_lookup(driver, wait)

    lookup_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )

    lookup_button.click()

    wait.until(
        EC.text_to_be_present_in_element(
            (By.ID, "lookup-result"),
            "Enter a patient ID before submitting.",
        )
    )

    assert "Enter a patient ID before submitting." in result_region(driver).text


def test_successful_patient_lookup_updates_the_live_result_region(driver, wait):
    """
    Parallel to Playwright:

    successful patient lookup updates the live result region
    """

    open_patient_lookup(driver, wait)

    lookup_patient(driver, wait, "1001")

    wait.until(
        EC.text_to_be_present_in_element(
            (By.ID, "lookup-result"),
            "Patient lookup succeeded for 1001.",
        )
    )

    assert "Patient lookup succeeded for 1001." in result_region(driver).text


def test_not_found_patient_lookup_reports_the_expected_status(driver, wait):
    """
    Parallel to Playwright:

    not-found patient lookup reports the expected status
    """

    open_patient_lookup(driver, wait)

    lookup_patient(driver, wait, "9999")

    wait.until(
        EC.text_to_be_present_in_element(
            (By.ID, "lookup-result"),
            "Patient lookup returned status 404.",
        )
    )

    assert "Patient lookup returned status 404." in result_region(driver).text
