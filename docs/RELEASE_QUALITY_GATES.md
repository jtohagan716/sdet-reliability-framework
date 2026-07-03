# Release Quality Gates

## Purpose

This project includes a release quality gate script that runs the major validation checks before a release is considered ready.

A quality gate is a required checkpoint that software must pass before moving forward.

In plain English:

    Do not release unless the required checks pass.

## Release Quality Gate Script

Script:

    scripts/run_release_quality_gate.ps1

Default command:

    .\scripts\run_release_quality_gate.ps1

Default report:

    reports/release_quality_gate_v0.9.0.md

## What the Gate Runs

The release quality gate currently runs:

| Gate | Purpose |
|---|---|
| Python syntax check - FastAPI app | Confirms the Application Programming Interface (API) app can be parsed |
| Python syntax check - performance baseline script | Confirms the performance baseline script can be parsed |
| Python syntax check - lightweight load test script | Confirms the lightweight load test script can be parsed |
| Full Pytest regression suite | Validates backend behavior and regression coverage |
| Start Docker stack | Confirms the local containerized runtime can start |
| Newman API regression | Validates the Postman Application Programming Interface (API) regression collection |
| Focused Section 508 accessibility smoke validation | Validates basic accessibility behavior on the Patient Lookup page |
| Full Playwright automation | Validates user interface (UI), Application Programming Interface (API), and workflow checks |
| performance baseline results | Captures known-good local response-time and error-rate results |
| lightweight load test results | Captures weighted concurrent traffic behavior |
| Local Docker/API smoke validation | Confirms Docker, API health, patient endpoints, Pytest, and Newman checks pass together |

## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL) Connection

This milestone maps to several formal testing concepts.

### Exit Criteria

Exit criteria define what must be true before testing or release activity can be considered complete.

For this project, release exit criteria include:

- syntax checks pass
- regression tests pass
- Application Programming Interface (API) checks pass
- Playwright automation passes
- accessibility smoke validation passes
- performance baseline results is generated
- lightweight load test results is generated
- Docker smoke validation passes

### Regression Testing

Regression testing confirms that existing behavior still works after changes are made.

The release quality gate runs regression checks through:

- Pytest
- Newman
- Playwright
- local smoke validation

### test results

test results is proof that validation was performed.

This project stores results in:

- generated reports
- terminal results
- GitHub Actions results
- release notes
- versioned GitHub releases

## Continuous Integration / Continuous Delivery (CI/CD) Connection

In a modern Continuous Integration / Continuous Delivery (CI/CD) workflow, quality gates help prevent weak changes from moving forward.

A failing gate should block release until the issue is understood and corrected.

This project currently runs the release quality gate locally. Future work can integrate more of this gate into GitHub Actions.

## Department of Homeland Security (DHS) / Section 508 Connection

Accessibility validation is included as part of release readiness.

The focused accessibility smoke validation checks basic behavior such as:

- page title
- heading
- accessible input label
- accessible button role/name
- keyboard reachability
- result-region feedback

This does not claim full Section 508 certification. It is a release-readiness smoke layer that can later be expanded with formal Department of Homeland Security (DHS) Trusted Tester practices.

## Reliability Value

The release quality gate helps replace ad hoc release decisions with repeatable validation results.

Instead of saying:

    I think it works.

The project can say:

    The required release checks passed, and a report was generated.

## Current Report

Current report:

    reports/release_quality_gate_v0.9.0.md

## Future Work

Possible improvements:

- Add GitHub Actions integration for the full release quality gate.
- Add threshold checks for p95 response time and error rate.
- Add automated comparison against prior performance baseline.
- Add axe-core accessibility scanning.
- Add Kubernetes deployment validation.
- Add release checklist documentation.



