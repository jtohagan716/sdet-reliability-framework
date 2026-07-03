# Certification Alignment

## Purpose

This document maps the project capabilities to formal software testing, accessibility, performance, and delivery concepts.

The purpose is to show how the project reinforces recognized testing and validation practices without claiming certification or formal compliance.

## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL)

The International Software Testing Qualifications Board (ISTQB) Certified Tester Foundation Level (CTFL) provides foundational software testing vocabulary and concepts.

This project reinforces several of those concepts through implementation and documentation.

### Regression Testing

Regression testing checks that existing behavior still works after changes are made.

Project examples:

- Pytest regression suite
- Newman Application Programming Interface (API) regression collection
- Playwright automation suite
- local smoke validation script
- release quality gate workflow

### Confirmation Testing

Confirmation testing verifies that a fix or intended behavior works as expected.

Project examples:

- expected successful patient lookup
- expected not-found response
- expected invalid-input response
- expected accessibility page behavior
- expected health-check behavior

### Acceptance Criteria

Acceptance criteria define what must be true for work to be considered complete.

Project examples:

- endpoint returns expected status code
- response body contains expected data
- accessibility smoke test passes
- performance report is generated
- release quality gate completes successfully

### Exit Criteria

Exit criteria define what must be true before a release or test phase is considered complete.

Project examples:

- syntax checks pass
- automated regression tests pass
- Application Programming Interface (API) checks pass
- Playwright checks pass
- accessibility smoke validation passes
- performance results is generated
- release quality gate report is generated

### test results

test results provides proof that validation was performed.

Project examples:

- generated Markdown reports
- GitHub Actions results
- release notes
- versioned tags
- release quality gate report

### Risk-Based Testing

Risk-based testing focuses validation effort on areas that could create meaningful failure or release risk.

Project examples:

- health-check validation
- patient lookup behavior
- expected error handling
- performance baseline results
- lightweight load testing
- accessibility smoke validation
- release quality gates

## Department of Homeland Security (DHS) / Section 508 Accessibility Concepts

Section 508 requires federal electronic and information technology to be accessible to users with disabilities.

This project does not claim full Section 508 certification or Department of Homeland Security (DHS) Trusted Tester coverage.

The project includes Section 508-oriented accessibility smoke validation.

### Accessible Name and Labeling

User-facing form controls should have accessible names and labels.

Project examples:

- Patient ID input has a visible label
- Lookup button is discoverable by role and name

### Keyboard Reachability

Interactive controls should be reachable without a mouse.

Project examples:

- Patient ID input can receive keyboard focus
- Lookup button can receive keyboard focus

### Page Structure

Pages should expose meaningful structure.

Project examples:

- document language is defined
- page title is present
- main heading is present
- instructions are visible

### Status and Feedback

User actions should provide understandable feedback.

Project examples:

- empty submission displays a validation message
- successful lookup updates the result region
- not-found lookup reports the expected status

### Accessibility as Release Readiness

Accessibility checks should be included before release, not treated as an afterthought.

Project examples:

- focused accessibility smoke validation
- accessibility report
- accessibility check included in the release quality gate

## Performance Testing Concepts

The project includes performance results at two levels.

### Performance Baseline

A performance baseline establishes a known-good reference point.

Project examples:

- response-time measurements
- expected status outcomes
- error-rate reporting
- p95 response-time reporting

### Lightweight Load Testing

A lightweight load test checks behavior under a small controlled traffic mix.

Project examples:

- weighted traffic mix
- concurrent requests
- throughput reporting
- p95 and p99 response-time reporting
- scenario-level breakdown

### Tail Latency

Tail latency focuses on slower outliers that may be hidden by averages.

Project examples:

- p95 response time
- p99 response time
- maximum response time

## Continuous Integration / Continuous Delivery (CI/CD) Concepts

Continuous Integration / Continuous Delivery (CI/CD) practices use automated checks to support reliable delivery.

### Automated Validation

Project examples:

- Pytest
- Newman
- Playwright
- local smoke validation
- release quality gate script

### Quality Gates

A quality gate is a required checkpoint before software moves forward.

Project examples:

- release quality gate script
- release quality gate report
- required validation sequence before release

### Release Results

Release results helps demonstrate that required checks were completed.

Project examples:

- generated reports
- GitHub releases
- version tags
- documented release notes

## Current Scope

This document describes conceptual alignment only.

It does not claim that the project grants certification, formal compliance, or production certification.

## Future Alignment Opportunities

Possible future improvements include:

- Department of Homeland Security (DHS) Trusted Tester study mapping
- Web Content Accessibility Guidelines (WCAG) checklist mapping
- axe-core accessibility scanning
- Kubernetes local deployment validation
- GitHub Actions quality gate expansion
- performance threshold enforcement
- baseline comparison reports



