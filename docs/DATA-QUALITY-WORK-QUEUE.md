## Summary

This release adds a PostgreSQL-backed Data Quality Work Queue to the SDET Reliability Framework.

The feature models durable asynchronous processing for patient data quality review events. It validates that work can be enqueued, safely claimed by a worker, protected from duplicate claims, completed, and preserved with queue processing history.

This release strengthens the project’s SRE- and reliability-testing story by adding queue-based processing behavior to the healthcare data quality workflow.

## Added

* PostgreSQL schema for `data_quality_work_queue`
* PostgreSQL schema for `data_quality_work_queue_history`
* SQL validation script for queue processing behavior
* Automated pytest validation for the work queue
* Documentation for the Data Quality Work Queue
* README documentation link

## Key Scenario

This release validates the following workflow:

```text
A patient data quality review item is created.

A durable queue item is created from the review item.

The queue item starts in ready status.

A synthetic worker claims the item using a row-locking pattern.

The queue item moves from ready to processing.

A duplicate claim attempt is prevented.

The worker completes the queue item.

The queue item moves from processing to completed.

Queue history preserves created, claimed, and completed actions.

The source review item remains unchanged.

The queue item remains linked to the source review item.
```

## Validation

Focused queue validation:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue.py -v
```

Related review queue validation:

```powershell
python -m pytest tests/integration/test_patient_data_quality_review_queue.py tests/integration/test_data_quality_work_queue.py -v
```

Manual SQL validation:

```powershell
Get-Content scripts\validate_data_quality_work_queue.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected assertions:

```text
duplicate_claim_prevention_assertion | passed
queue_completion_assertion | passed
queue_history_assertion | passed
review_item_unchanged_assertion | passed
queue_linkage_assertion | passed
ROLLBACK
```

## Reliability Value

This release demonstrates:

* durable queue storage
* asynchronous work processing
* worker claim behavior
* duplicate processing prevention
* queue state transition validation
* queue processing history
* source review item linkage
* repeatable database validation
* operational support visibility

This is relevant to Software Development Engineer in Test (SDET), Site Reliability Engineering (SRE), healthcare integration testing, application support, production support, and data quality validation roles.

## Scope

This project uses synthetic healthcare-style data only.

It does not use real patient data, protected health information, production credentials, or production database exports.

It is not a production healthcare system, Electronic Health Record, clinical decision system, provider workflow platform, full FHIR implementation, FHIR conformance suite, or Oracle Advanced Queuing implementation.
