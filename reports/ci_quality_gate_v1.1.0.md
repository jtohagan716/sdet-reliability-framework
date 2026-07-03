# CI Quality Gate v1.1.0

## Summary

This release expands the Continuous Integration (CI) validation workflow for the SDET Reliability Framework.

The workflow now provides clearer automated validation across Docker build checks, Python regression tests, Application Programming Interface (API) validation, Playwright automation, accessibility smoke validation, and uploaded test result artifacts.

## CI Workflow Updates

| Area | Update |
|---|---|
| Manual workflow runs | Added workflow_dispatch support |
| Docker validation | Docker image build validation remains part of CI |
| Python validation | Pytest now generates a JUnit XML result file |
| API validation | Newman/Postman result artifact upload remains part of CI |
| Playwright validation | Playwright now generates a JUnit XML result file |
| Accessibility validation | Patient Lookup accessibility smoke test is included in CI |
| Result artifacts | Pytest, Newman, and Playwright results are uploaded as workflow artifacts |

## Validation Jobs

### Docker Build Validation

Confirms that the application Docker image can be built successfully.

### Python Reliability Tests

Runs the Python regression suite and performance CI gate.

Generated result artifact:

    reports/pytest-results.xml

### API and UI Validation

Starts the Docker Compose stack, validates the Application Programming Interface (API) with Newman, and runs the focused Playwright automation suite.

Generated result artifacts:

    reports/postman-newman-results.xml
    reports/playwright-results.xml

## Accessibility Smoke Validation

The CI workflow now includes:

    tests/ui/patient_lookup_accessibility.spec.ts

This keeps Section 508-oriented accessibility smoke validation in the automated validation path.

This does not claim full Section 508 certification. It confirms that the accessibility smoke checks are part of the regular CI workflow.

## Local Validation Completed

The following local checks passed before this update was committed:

    python -m pytest
    npm run postman:test
    npx playwright test tests/ui/patient_lookup_accessibility.spec.ts

## Current Scope

This release improves CI validation structure and result artifact collection.

It does not add a new application feature.
