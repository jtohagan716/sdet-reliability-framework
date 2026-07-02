# Section 508-Oriented Accessibility Smoke Validation

## Purpose

This project includes basic accessibility smoke validation for a simple user-facing Patient Lookup page.

The goal is to demonstrate awareness of accessibility and Section 508-oriented testing practices in a controlled portfolio-scale application.

This is not a full formal Section 508 certification. It is a first automated accessibility smoke layer.

## Page Under Test

Endpoint:

    /patient-lookup

The page includes:

- document language
- page title
- main heading
- instructions
- labeled Patient ID input
- submit button
- live result region
- keyboard-friendly form behavior

## Why This Matters

Federal software platforms often require accessibility validation. Section 508 testing helps ensure that users with disabilities can access and interact with electronic information and systems.

For this project, the accessibility smoke test checks whether the page exposes basic semantic structure and keyboard interaction expected in accessible web applications.

## Agile Testing Context

This work supports the following reliability and accessibility story:

As a reliability-focused QA/SDET, I want to validate basic accessibility behavior on a user-facing page, so that accessibility issues can be detected early as part of automated regression testing.

## Acceptance Criteria

- A simple user-facing Patient Lookup page is available.
- The page has a title and main heading.
- The Patient ID input has an accessible label.
- The submit button is discoverable by role and name.
- The result area is available as a named region.
- The input and button are keyboard reachable.
- Form submissions produce user-visible feedback.
- Automated Playwright smoke tests validate the page behavior.
- Pytest validates that the page returns accessible HTML structure.
- Existing project regression checks continue to pass.

## Test Files

Playwright accessibility smoke validation:

    tests/ui/patient_lookup_accessibility.spec.ts

FastAPI/Pytest page validation:

    tests/test_patient_lookup_page.py

## Commands

Run the focused Playwright accessibility smoke test:

    npx playwright test tests/ui/patient_lookup_accessibility.spec.ts

Run the focused Pytest page validation:

    python -m pytest tests/test_patient_lookup_page.py

Run the full Pytest suite:

    python -m pytest

## What the Playwright Tests Validate

The Playwright tests validate:

- page title
- heading
- visible instructions
- accessible input label
- accessible button role/name
- named result region
- keyboard tab order
- empty-submit feedback
- successful lookup feedback
- not-found lookup feedback

## What This Does Not Claim

This project does not claim full Section 508 certification.

This smoke validation does not replace:

- formal accessibility audit
- DHS Trusted Tester procedure
- manual screen reader testing
- color contrast review
- full WCAG analysis

## Future Work

Possible future improvements:

- add axe-core accessibility scans
- add color contrast checks
- add keyboard-only workflow documentation
- add screen reader testing notes
- add CI accessibility quality gate
- add Section 508 checklist documentation
