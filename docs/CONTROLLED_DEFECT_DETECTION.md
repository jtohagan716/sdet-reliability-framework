# Controlled Defect Detection Validation

## Purpose

Controlled defect detection validates that the framework can detect a meaningful business-rule failure, not only confirm passing behavior.

This milestone focuses on the patient lookup `last_visit` rule.

## Business Rule

`last_visit` must be calculated from completed encounters only.

Scheduled encounters must not affect `last_visit`.

## Controlled Defect

The controlled defect intentionally changes patient lookup behavior so that `last_visit` includes scheduled encounters.

This is controlled by the API environment variable:

    PATIENT_LOOKUP_DEFECT_MODE

Default behavior:

    PATIENT_LOOKUP_DEFECT_MODE=none

Controlled defect behavior:

    PATIENT_LOOKUP_DEFECT_MODE=include_scheduled_last_visit

## Why Patient 1004 Is Used

Synthetic patient `1004` has both a completed encounter and a scheduled encounter.

| Patient ID | Completed Encounter | Scheduled Encounter |
|---|---|---|
| 1004 | 2026-04-02 | 2026-07-20 |

Correct behavior returns:

    last_visit = 2026-04-02

Defective behavior returns:

    last_visit = 2026-07-20

This makes patient `1004` a useful validation case because the defect produces a clear API-to-database mismatch.

## Validation Flow

The controlled defect detection script performs the following sequence:

1. Start the normal Docker Compose stack.
2. Confirm `PATIENT_LOOKUP_DEFECT_MODE=none`.
3. Run API-to-database consistency validation and confirm it passes.
4. Restart the API container with `PATIENT_LOOKUP_DEFECT_MODE=include_scheduled_last_visit`.
5. Confirm patient `1004` returns a different `last_visit` than the correct database rule.
6. Run API-to-database consistency validation and confirm it fails.
7. Restore `PATIENT_LOOKUP_DEFECT_MODE=none`.
8. Run API-to-database consistency validation again and confirm it passes.

## Validation Script

The validation script is:

    scripts/validate_controlled_defect_detection.ps1

Run it with:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_controlled_defect_detection.ps1

## Expected Result

The expected successful result is:

    Controlled defect detection validation passed.

This means the framework confirmed both sides of the behavior:

- normal behavior passes validation
- controlled defective behavior fails validation
- normal behavior is restored and passes again

## Scope

This validation intentionally uses a controlled defect mode for local testing.

The controlled defect mode is disabled by default.

This is not a production feature. It exists to demonstrate that the validation layer can detect a business-rule failure.

## Data Safety

All data is synthetic.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
