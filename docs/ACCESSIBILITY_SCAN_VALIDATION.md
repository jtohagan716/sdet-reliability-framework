# Accessibility Scan Validation

## Summary

This document describes the automated accessibility scan validation added to the SDET Reliability Framework.

The project already includes Section 508-oriented accessibility smoke validation for the Patient Lookup page. This update adds an automated axe-core accessibility scan through Playwright.

The scan helps identify automatically detectable accessibility issues on the rendered page.

## Purpose

The purpose of this validation layer is to strengthen accessibility testing by adding an automated rules-based scan.

The scan checks the Patient Lookup page against selected WCAG rule tags through axe-core.

Validated tags include:

- wcag2a
- wcag2aa
- wcag21a
- wcag21aa

## Test File

The accessibility scan test is located at:

    tests/ui/patient_lookup_axe_accessibility.spec.ts

Run the scan locally with:

    npx playwright test tests/ui/patient_lookup_axe_accessibility.spec.ts --project=chromium

## Validated Page

| Page | Purpose |
|---|---|
| /patient-lookup | Patient Lookup accessibility scan |

## Relationship to Existing Accessibility Smoke Testing

The existing accessibility smoke test checks known page behaviors, including:

- page title
- heading
- input label
- button role and name
- keyboard reachability
- result-region feedback

The axe-core scan adds a broader automated accessibility check against the rendered page.

Both layers are useful:

| Layer | Purpose |
|---|---|
| Accessibility smoke test | Confirms expected page-specific accessibility behavior |
| axe-core scan | Detects automatically identifiable accessibility rule violations |

## Current Scope

This scan does not claim full Section 508 certification.

It provides automated accessibility scan coverage for the current Patient Lookup page and can be expanded as additional pages or workflows are added.
