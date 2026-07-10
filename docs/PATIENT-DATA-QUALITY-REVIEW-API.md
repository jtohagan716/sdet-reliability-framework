# Patient Data Quality Review API

## Purpose

The Patient Data Quality Review API exposes patient data quality review items through read-only application endpoints.

This feature connects the PostgreSQL-backed review queue to the FastAPI application layer.

The goal is to demonstrate that database-backed reliability evidence can be surfaced through a controlled API without building a full Electronic Health Record (EHR), clinical workflow system, or production healthcare application.

## What This Feature Demonstrates

This feature shows that the framework can validate:

```text
database-backed review evidence
+ read-only API access
+ review item filtering
+ review action history
+ invalid input handling
+ not-found handling
+ automated API validation
```

It extends the Patient Data Quality Review Queue by proving that review items are not only stored in PostgreSQL. They can also be queried through the application layer.

## Endpoints Added

### List Review Items

```text
GET /qa/data-quality-review-items
```

Optional query parameters:

```text
review_status
limit
```

Example:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items?review_status=confirmed_correct&limit=10"
```

The endpoint returns:

```text
review_items
count
```

Each review item includes fields such as:

```text
review_item_key
review_source
patient_reference
encounter_reference
related_event_id
related_decision_id
review_reason
risk_summary
review_priority
review_status
assigned_role
assigned_to
reviewed_by
review_outcome
review_notes
details
```

### Get Review Item Detail

```text
GET /qa/data-quality-review-items/{review_item_key}
```

Example:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items/dq-review-api-encounter-example-001-stale-message"
```

The detail endpoint returns the review item plus its action history.

Important response fields include:

```text
review_item_key
patient_reference
encounter_reference
review_status
review_outcome
actions
```

The `actions` array preserves review history such as:

```text
created
confirmed_correct
```

## Review Status Validation

The API accepts these review statuses:

```text
pending_review
confirmed_correct
flagged_incorrect
needs_reconciliation
closed
```

Invalid statuses are rejected.

Example:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items?review_status=bad_status"
```

Expected response:

```text
INVALID_REVIEW_STATUS
```

This validates that the API rejects unsupported review states instead of silently returning misleading results.

## Missing Item Handling

The detail endpoint returns a not-found response when a review item key does not exist.

Example:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items/missing-review-item"
```

Expected response:

```text
REVIEW_ITEM_NOT_FOUND
```

## Files Added

Repository layer:

```text
api_service/repositories/data_quality_reviews.py
```

API endpoint updates:

```text
api_service/app.py
```

Demo seed data:

```text
scripts/seed_patient_data_quality_review_queue_api_demo.sql
```

Automated validation:

```text
tests/integration/test_patient_data_quality_review_queue_api.py
```

## Demo Seed Data

The API demo seed creates a synthetic review item:

```text
dq-review-api-encounter-example-001-stale-message
```

The seeded workflow models this scenario:

```text
A newer complete Encounter message is accepted.

An older partial Encounter message arrives later.

The older partial message is archived as stale.

The current Encounter state remains protected.

A patient data quality review item is created.

A Data Quality Expert confirms the software decision as correct.

The review action history is preserved.
```

The demo uses:

```text
review_status: confirmed_correct
review_outcome: software_decision_correct
assigned_role: Data Quality Expert
```

## Manual Validation

Apply required schemas and seed data:

```powershell
Get-Content db\sql\010_fhir_stale_message_evidence.sql | docker compose exec -T postgres psql -U sdet_user -d sdet_reliability
Get-Content db\sql\011_patient_data_quality_review_queue.sql | docker compose exec -T postgres psql -U sdet_user -d sdet_reliability
Get-Content scripts\seed_patient_data_quality_review_queue_api_demo.sql | docker compose exec -T postgres psql -U sdet_user -d sdet_reliability
```

Rebuild and restart the API:

```powershell
docker compose build api
docker compose up -d api
docker compose ps
```

Test the list endpoint:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items?review_status=confirmed_correct&limit=10"
```

Test the detail endpoint:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items/dq-review-api-encounter-example-001-stale-message"
```

Test invalid status handling:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items?review_status=bad_status"
```

Test missing item handling:

```powershell
Invoke-RestMethod "http://localhost:8000/qa/data-quality-review-items/missing-review-item"
```

## Automated Validation

Run the focused API test:

```powershell
python -m pytest tests/integration/test_patient_data_quality_review_queue_api.py -v
```

Run the review queue and API validation together:

```powershell
python -m pytest tests/integration/test_patient_data_quality_review_queue.py tests/integration/test_patient_data_quality_review_queue_api.py -v
```

## Reliability Value

This feature demonstrates:

```text
read-only API validation
database-backed evidence access
review item filtering
review action history retrieval
invalid input handling
not-found handling
healthcare-style data quality visibility
application-layer access to review evidence
```

The feature shows that data quality review evidence can be stored, queried, and validated across both the database and API layers.

## Scope

This API uses synthetic healthcare-style data.

It does not use real patient data, protected health information, production credentials, or production database exports.

It is not a production healthcare system, EHR, clinical decision system, provider workflow platform, full FHIR implementation, or FHIR conformance suite.

## Summary

The Patient Data Quality Review API extends the review queue by exposing review items through read-only FastAPI endpoints.

It connects PostgreSQL evidence to application behavior and validates that reviewable healthcare-style data quality decisions can be queried safely through an API.
