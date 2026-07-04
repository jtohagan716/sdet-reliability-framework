# Accessibility Scan Validation v1.3.0

## Summary

This release adds automated accessibility scan validation to the SDET Reliability Framework.

The new Playwright test uses axe-core to scan the Patient Lookup page for automatically detectable accessibility violations.

## Added

| Item | Description |
|---|---|
| axe-core dependency | Added @axe-core/playwright |
| Accessibility scan test | Added Playwright axe-core scan for /patient-lookup |
| CI validation | Added the axe accessibility scan to the CI Playwright validation path |
| Documentation | Added accessibility scan validation documentation |

## Test File

    tests/ui/patient_lookup_axe_accessibility.spec.ts

## Validation Command

Run the accessibility scan locally with:

    npx playwright test tests/ui/patient_lookup_axe_accessibility.spec.ts --project=chromium

## Local Validation Result

The accessibility scan passed locally against the running Docker Compose application stack.

## Current Scope

This release adds automated accessibility scan coverage for the Patient Lookup page.

It does not claim full Section 508 certification and does not replace manual accessibility review.
