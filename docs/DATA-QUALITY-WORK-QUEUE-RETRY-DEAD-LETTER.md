# Data Quality Work Queue Retry and Dead-Letter Validation

## Purpose

The Data Quality Work Queue Retry and Dead-Letter Validation feature demonstrates how the PostgreSQL-backed work queue behaves when processing fails.

This extends the base Data Quality Work Queue by validating failure handling, retry scheduling, maximum attempt enforcement, and dead-letter preservation.

The goal is to prove that queue processing is not only successful on the happy path, but also reliable and inspectable when workers fail.

This is an important Site Reliability Engineering (SRE), Software Development Engineer in Test (SDET), and operational support pattern.

## Why This Matters

Real systems fail.

A queue worker may be unable to process a work item because of:

```text
transient downstream failure
database issue
mapping issue
bad payload
external dependency failure
worker crash
unexpected processing error
```

A reliable queue should not silently lose the work item.

It should preserve what happened, track attempts, schedule retry when appropriate, and move persistent failures to a dead-letter state for review.

This feature validates that behavior with synthetic healthcare-style data.

## What This Feature Demonstrates

This feature proves that:

```text
A worker can claim a ready work item.

A processing failure can be recorded.

The attempt count is preserved.

The work item can become retryable when attempts remain.

A second worker can claim the retry.

A second failure can be recorded.

Maximum attempts are enforced.

The work item moves to dead_letter after max attempts.

The final error reason is preserved.

Queue history records each transition.

The source review item remains unchanged.

The validation remains repeatable through ROLLBACK.
```

## Queue Failure Path

The validated status flow is:

```text
ready
-> processing
-> failed
-> ready
-> processing
-> failed
-> dead_letter
```

This proves more than a successful queue path.

It validates operational failure behavior.

## Tables Used

This feature uses the PostgreSQL-backed queue tables introduced by the Data Quality Work Queue feature:

```text
data_quality_work_queue
data_quality_work_queue_history
```

### data_quality_work_queue

This table stores the current state of the work item.

Important fields for retry and dead-letter behavior include:

```text
work_item_key
status
attempt_count
max_attempts
available_at
locked_at
locked_by
processed_at
error_message
updated_at
```

### data_quality_work_queue_history

This table preserves the transition history.

Important fields include:

```text
work_item_key
previous_status
new_status
action_type
action_by
action_note
details
```

The history table is critical because the final state alone does not explain the full failure path.

## Scenario Validated

The validation script models this workflow:

```text
1. A patient data quality review item is created.
2. A durable work queue item is created with max_attempts set to 2.
3. The work item starts in ready status.
4. Worker 1 claims the item.
5. The item moves from ready to processing.
6. Worker 1 fails processing.
7. The item moves from processing to failed.
8. Retry is scheduled because attempt_count is below max_attempts.
9. The item moves from failed back to ready.
10. Worker 2 claims the retry.
11. The item moves from ready to processing.
12. Worker 2 fails processing.
13. The item moves from processing to failed.
14. The retry policy detects that max_attempts has been reached.
15. The item moves from failed to dead_letter.
16. The final error reason is preserved.
17. Queue history records all transitions.
18. The source review item remains unchanged.
19. The transaction rolls back for repeatable validation.
```

## History Actions Validated

The queue history records these action types:

```text
created
claimed
failed
retry_scheduled
claimed
failed
moved_to_dead_letter
```

The expected count is seven history records.

That confirms that the failure path is not hidden.

## Assertions Validated

The manual SQL validation checks:

```text
retry_attempt_assertion
dead_letter_assertion
retry_history_assertion
review_item_unchanged_assertion
queue_linkage_assertion
```

Expected result:

```text
retry_attempt_assertion | passed
dead_letter_assertion | passed
retry_history_assertion | passed
review_item_unchanged_assertion | passed
queue_linkage_assertion | passed
ROLLBACK
```

## Files Added

Manual validation script:

```text
scripts/validate_data_quality_work_queue_retry_dead_letter.sql
```

Automated validation:

```text
tests/integration/test_data_quality_work_queue_retry_dead_letter.py
```

Related base queue files:

```text
db/sql/012_data_quality_work_queue.sql
scripts/validate_data_quality_work_queue.sql
tests/integration/test_data_quality_work_queue.py
docs/DATA-QUALITY-WORK-QUEUE.md
```

## Manual SQL Validation

Run:

```powershell
Get-Content scripts\validate_data_quality_work_queue_retry_dead_letter.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected assertions:

```text
retry_attempt_assertion | passed
dead_letter_assertion | passed
retry_history_assertion | passed
review_item_unchanged_assertion | passed
queue_linkage_assertion | passed
ROLLBACK
```

## Automated Validation

Run the focused retry/dead-letter test:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue_retry_dead_letter.py -v
```

Run it with the base queue validation:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py -v
```

## Why ROLLBACK Is Used

The validation script ends with:

```sql
ROLLBACK;
```

This is intentional.

The script proves the failure path without leaving behind test records that could interfere with later test runs.

This keeps the validation repeatable and deterministic.

## Reliability Value

This feature demonstrates:

```text
worker failure handling
retry scheduling
attempt count tracking
maximum attempt enforcement
dead-letter preservation
error reason preservation
queue transition history
source review item protection
repeatable database validation
operational support visibility
```

This is directly relevant to SRE, SDET, production support, application support, healthcare integration testing, and data quality validation roles.

## Relationship to Healthcare Data Quality

Healthcare data quality issues may require background processing, reconciliation, mapper review, or operational investigation.

If that background work fails, the system should preserve the failure evidence.

The dead-letter state gives support teams a clear place to look for work that could not be completed automatically.

This is safer than silently dropping failed processing attempts.

## Relationship to Oracle Advanced Queuing Concepts

This project does not implement Oracle Advanced Queuing.

However, this feature models a similar reliability concern:

```text
durable work exists
workers claim work
processing can fail
retry policy is applied
persistent failure is preserved for review
history explains what happened
```

In this project, the behavior is modeled with PostgreSQL tables, row-based state transitions, and repeatable SQL validation.

## Scope

This feature uses synthetic healthcare-style data.

It does not use real patient data, protected health information, production credentials, or production database exports.

It does not claim to be:

```text
a production healthcare system
an Electronic Health Record
a clinical decision system
a provider workflow platform
a full FHIR implementation
a FHIR conformance suite
an Oracle Advanced Queuing implementation
```

The feature is a controlled reliability validation scenario.

## Future Enhancements

Possible future improvements include:

```text
dead-letter review API
dead-letter reconciliation export
queue health endpoint
Prometheus metrics for retry and dead-letter counts
OpenTelemetry tracing for queue processing
operator runbook for dead-letter investigation
manual requeue workflow
LISTEN/NOTIFY worker wake-up demonstration
```

## Summary

The Data Quality Work Queue Retry and Dead-Letter Validation feature proves that queue failures are handled visibly and repeatably.

It validates retry scheduling, maximum attempt enforcement, dead-letter preservation, error reason capture, and queue history.

This strengthens the project’s SRE and reliability-testing story by showing how the system behaves when background processing fails.
