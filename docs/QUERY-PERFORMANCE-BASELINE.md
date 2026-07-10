# Query Performance Baseline Validation

## Purpose

The Query Performance Baseline Validation feature establishes the first repeatable performance baseline for the healthcare data quality workflow.

The goal is not to tune the query yet.

The goal is to measure first, capture evidence, and create a trustworthy baseline that future tuning work can compare against.

This supports a disciplined performance workflow:

```text
measure first
understand the query plan
avoid premature tuning
change one thing later
compare before and after
document the tradeoff
```

## Why This Matters

Performance tuning should not begin with guessing.

Before adding indexes, changing queries, adjusting database settings, or changing application behavior, the system needs a known baseline.

This feature captures:

```text
PostgreSQL query plan
planning time
execution time
buffer usage
rows returned
queue linkage
queue status distribution
repeatable validation evidence
```

The validation uses synthetic healthcare-style data and rolls back at the end so the test remains deterministic and repeatable.

## Baseline Scenario

The baseline query models a realistic healthcare data quality support workflow.

A data quality or operational user needs to retrieve:

```text
pending high-priority patient data quality review items
related patient reference
related encounter reference
assigned role
related queue work item
current queue status
attempt count
maximum attempts
```

This answers an operational question:

```text
Which high-priority data quality review items are pending, and what is the related background queue state?
```

## Tables Used

The baseline query uses:

```text
patient_data_quality_review_items
data_quality_work_queue
```

The query joins review items to queue work items using:

```text
data_quality_work_queue.source_review_item_key = patient_data_quality_review_items.review_item_key
```

## Query Shape

The baseline query filters review items by:

```text
review_status = 'pending_review'
review_priority = 'high'
```

It then left joins queue work item state and orders the results by:

```text
review.created_at
review.review_item_key
```

The purpose is to model a reviewer-facing or support-facing query where high-priority pending work is displayed with queue context.

## Synthetic Data Created

The validation script creates:

```text
25 synthetic patient data quality review items
25 matching data quality work queue items
```

The expected high-priority pending review result set contains:

```text
10 review items
10 matching queue items
8 ready queue items
2 processing queue items
```

## Metrics Captured

The validation captures PostgreSQL `EXPLAIN ANALYZE` output with buffer information.

The important evidence includes:

```text
query plan shape
scan type
join type
sort method
planning time
execution time
shared buffer hits
actual rows
estimated rows
rows removed by filter
```

## Baseline Observed Behavior

In the local validation environment, PostgreSQL selected:

```text
sequential scan on data_quality_work_queue
sequential scan on patient_data_quality_review_items
hash right join
quicksort
```

This is acceptable for the current small synthetic dataset.

Sequential scans are not automatically bad. For small tables, PostgreSQL may reasonably choose a sequential scan because scanning the table can be cheaper than using an index.

## Warm-Up Observation

The initial manual run showed higher timing than the repeated runs.

The repeated runs stabilized significantly after the first execution.

This suggests that the first run included cold-start or first-run overhead rather than steady-state query cost.

Example observed pattern:

```text
Initial run:
Planning Time: higher
Execution Time: higher

Repeated runs:
Planning Time: lower
Execution Time: lower
```

This is an important performance lesson.

A single run proves that the script works, but repeated runs provide better evidence about whether the measurement is stable or noisy.

## Assertions Validated

The validation checks:

```text
baseline_row_count_assertion
queue_linkage_assertion
queue_status_distribution_assertion
no_tuning_applied_assertion
```

Expected result:

```text
baseline_row_count_assertion | passed
queue_linkage_assertion | passed
queue_status_distribution_assertion | passed
no_tuning_applied_assertion | passed
ROLLBACK
```

## Why No Hard Timing Threshold Is Used

This feature intentionally does not assert that the query must run below a specific millisecond threshold.

Local timing can vary because of:

```text
Docker Desktop state
host machine load
first-run cache effects
PostgreSQL catalog/cache warm-up
container resource conditions
CI environment differences
```

A fragile test such as “execution time must be below 1 ms” would create noise and false failures.

Instead, this baseline validates that:

```text
the query plan is captured
planning time is present
execution time is present
buffer information is present
expected rows are returned
queue linkage is correct
queue status distribution is correct
no tuning is applied
the transaction rolls back cleanly
```

This creates a stable foundation for future before-and-after tuning comparison.

## Manual Validation

Run:

```powershell
Get-Content scripts\validate_query_performance_baseline.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected assertions:

```text
baseline_row_count_assertion | passed
queue_linkage_assertion | passed
queue_status_distribution_assertion | passed
no_tuning_applied_assertion | passed
ROLLBACK
```

## Automated Validation

Run the focused performance baseline test:

```powershell
python -m pytest tests/integration/test_query_performance_baseline.py -v
```

Run it with related queue validations:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py tests/integration/test_query_performance_baseline.py -v
```

## Current Interpretation

The current small local dataset does not justify tuning yet.

The correct interpretation is:

```text
The baseline query is functionally correct and repeatable.
PostgreSQL selected sequential scans and a hash join for a small local dataset.
Repeated runs stabilized after first-run overhead.
No tuning should be applied until additional evidence or larger data volume justifies it.
```

## Future Pre/Post Tuning Report

Future tuning work should compare this baseline against a post-change result.

The future report should include:

```text
before query plan
after query plan
before planning time
after planning time
before execution time
after execution time
before scan type
after scan type
before buffer usage
after buffer usage
delta comparison
interpretation
limitations
recommendation
```

Even if the measured improvement is negligible, the report should still document the result honestly.

The value is not inflated benchmark claims.

The value is repeatable performance analysis.

## Future Metrics and Risk Indicators

Future performance work should collect additional supporting metrics, including:

```text
API latency
p95 and p99 response time
queue depth
oldest ready queue item age
retry count
dead-letter count
database lock waits
container CPU usage
container memory usage
context switching where available
test runtime
CI job duration
```

Some metrics may not indicate a problem in the local validation environment but could still become production monitoring candidates under higher data volume or concurrency.

A useful report phrase is:

```text
This metric was not a failure condition in the local validation environment, but it is a production monitoring candidate under higher concurrency or larger data volume.
```

## Reliability Value

This feature demonstrates:

```text
performance baseline discipline
query plan capture
evidence-first tuning mindset
repeatable SQL validation
safe use of ROLLBACK
avoidance of premature tuning
healthcare data quality workflow measurement
foundation for future pre/post performance reports
```

This is relevant to Software Development Engineer in Test (SDET), Site Reliability Engineering (SRE), application support, production support, healthcare integration testing, and database-backed reliability validation roles.

## Scope

This feature uses synthetic healthcare-style data only.

It does not use real patient data, protected health information, production credentials, or production database exports.

It does not claim production-scale performance results or database administrator-level tuning.

It establishes a repeatable local performance baseline for future comparison.

## Summary

Query Performance Baseline Validation establishes the first performance measurement foundation for the project.

It captures a PostgreSQL query plan, validates expected workflow results, confirms queue linkage, records timing evidence, and avoids premature tuning.

This is the first step toward evidence-based performance analysis across the API, database, queue, observability, and CI layers.
