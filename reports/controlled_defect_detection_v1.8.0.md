# v1.8.0 - Controlled Defect Detection Validation

## Summary

This milestone adds controlled defect detection for the patient lookup API path.

The goal is to prove that the validation framework can detect a meaningful business-rule defect, not only confirm passing behavior.

## Business Rule

`last_visit` must be calculated from completed encounters only.

Scheduled encounters must not affect `last_visit`.

## Controlled Defect Mode

The API now supports a controlled defect mode through the following environment variable:

    PATIENT_LOOKUP_DEFECT_MODE

Default mode:

    none

Controlled defect mode:

    include_scheduled_last_visit

When the controlled defect mode is enabled, the patient lookup query incorrectly includes scheduled encounters when calculating `last_visit`.

## Test Patient

Synthetic patient `1004` is used because the seed data contains both completed and scheduled encounter records.

| Patient ID | Correct Completed Last Visit | Defective All-Status Last Visit |
|---|---|---|
| 1004 | 2026-04-02 | 2026-07-20 |

This creates a clear mismatch when the defect mode is enabled.

## Added

- Controlled patient lookup defect mode
- API environment variable for defect mode control
- Logging of patient lookup defect mode
- Controlled defect detection validation script
- Documentation for controlled defect detection behavior
- v1.8.0 controlled defect detection report

## Validation Flow

The validation script confirms:

1. Normal patient lookup behavior passes API-to-database consistency validation.
2. Controlled defect mode can be enabled intentionally.
3. Patient `1004` exposes the `last_visit` mismatch.
4. API-to-database consistency validation fails when the controlled defect is enabled.
5. Normal behavior can be restored.
6. API-to-database consistency validation passes again after restoration.

## Local Validation Command

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_controlled_defect_detection.ps1

## Expected Result

    Controlled defect detection validation passed.

## Why This Matters

A validation framework is more useful when it can prove that it detects failures.

This milestone demonstrates that the API-to-database consistency validation can catch a real business-rule mismatch involving completed and scheduled encounter data.

## Scope

This is a controlled local validation mechanism.

The defect mode is disabled by default.

The controlled defect mode is not intended for production use.

## Data Safety

All data is synthetic.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
