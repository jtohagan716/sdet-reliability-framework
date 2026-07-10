# Queue Performance Metrics Baseline

## Purpose

The Queue Performance Metrics Baseline feature establishes repeatable operational visibility into background work queue health.

This feature does not run a throughput test.

It does not attempt to prove maximum queue processing capacity.

Instead, it captures the baseline queue health signals that help determine whether background work is healthy, backing up, retrying too often, or accumulating dead-letter items.

The guiding idea is:

```text id="qwar7n"
A queue can be technically working while still becoming operationally unhealthy.
```

This feature makes those early warning signs visible.

## Why This Matters

Background queues are common in modern systems because they allow slower or riskier work to happen outside the user-facing request path.

A queue-based system needs more than functional tests.

Functional testing can prove:

```text id="3tesd6"
Can a work item be created?
Can a worker claim it?
Can a worker complete it?
Can failed work retry?
Can max-attempt failures move to dead-letter?
```

Operational reliability testing asks additional questions:

```text id="ptjlre"
How many items are waiting?
How many items are currently processing?
How many failed items are retry-eligible?
How many items are dead-lettered?
How old is the oldest ready item?
How long has the oldest processing item been locked?
Are retry and dead-letter events visible in history?
Is the queue quietly accumulating risk?
```

This feature begins answering those operational questions with deterministic synthetic data and rollback-safe validation.

## Relationship to Previous Queue Features

This feature builds on earlier queue work:

```text id="1lf6wu"
v2.3.0 — Data Quality Work Queue
v2.4.0 — Work Queue Retry and Dead-Letter Validation
```

Those features proved that the queue can:

```text id="x3h0my"
enqueue durable work
claim work safely
prevent duplicate claims
complete work
record history
retry failed work
move exhausted failures to dead-letter
preserve the source review item
```

This feature adds baseline visibility into the health of that queue.

It shifts the question from:

```text id="4haibz"
Does the queue behavior work?
```

to:

```text id="f5dpmb"
What is the operational state of the queue?
```

## Relationship to Performance Work

This feature also follows:

```text id="cziccm"
v2.5.0 — Query Performance Baseline Validation
v2.6.0 — Query Performance Tuning Comparison
v2.7.0 — API Endpoint Performance Baseline
```

The project now has baseline evidence across multiple layers:

```text id="nvl1fc"
database query behavior
database tuning comparison
API endpoint response behavior
background queue health
```

That starts forming a practical reliability diagnostics view.

## Scenario

The validation models a healthcare data quality support workflow.

A patient data quality review item creates background work.

The queue tracks the work through states such as:

```text id="1bhj43"
ready
processing
completed
failed
dead_letter
```

The validation creates deterministic synthetic queue data across those statuses so queue health metrics can be calculated and verified.

## Synthetic Dataset

The validation creates:

```text id="nsty3i"
30 synthetic patient data quality review items
30 synthetic work queue items
queue history records for created, claimed, completed, failed, retry, and dead-letter actions
```

The queue status distribution is deterministic:

```text id="8sifgn"
ready: 10
processing: 5
completed: 7
failed: 4
dead_letter: 4
total: 30
```

The failed items are retry-eligible because their attempt count is below the maximum attempt count.

The dead-letter items have reached the maximum attempt count and have a processed timestamp.

## Metrics Captured

The validation captures queue status metrics:

```text id="xc2h63"
queue_total_count
queue_ready_count
queue_processing_count
queue_completed_count
queue_failed_count
queue_dead_letter_count
```

It captures retry and attempt metrics:

```text id="r52fcb"
queue_retry_eligible_count
queue_max_attempt_count
queue_average_attempt_count
```

It captures backlog age metrics:

```text id="v31y7b"
oldest_ready_item_age_minutes
oldest_processing_item_age_minutes
queue_age_under_15_min_count
queue_age_15_to_45_min_count
queue_age_over_45_min_count
```

It captures history action metrics:

```text id="vg07oj"
history_created_count
history_claimed_count
history_completed_count
history_failed_count
history_retry_scheduled_count
history_moved_to_dead_letter_count
```

## Why Queue Age Matters

Queue depth alone is not enough.

A queue with 100 ready items might be fine if items are only a few seconds old.

A queue with 3 ready items might be a problem if the oldest ready item has been waiting for hours.

That is why this feature captures:

```text id="ys2r13"
oldest_ready_item_age_minutes
```

Processing age matters too.

A processing item may be healthy if it was locked a few seconds ago.

A processing item may be stuck if it has been locked for too long.

That is why this feature captures:

```text id="ng3mwu"
oldest_processing_item_age_minutes
```

These are early warning indicators.

## Why Retry Pressure Matters

Failed work is not automatically bad.

Temporary failures happen.

The key question is whether failures are retry-eligible, repeatedly failing, or exhausted.

This feature captures:

```text id="f7kpov"
queue_retry_eligible_count
queue_max_attempt_count
queue_average_attempt_count
```

Those metrics help distinguish normal transient retry behavior from unhealthy retry pressure.

## Why Dead-Letter Count Matters

Dead-letter items are work items that could not be processed successfully after the allowed retry attempts.

They matter because they usually require inspection, correction, replay, or manual intervention.

This feature captures:

```text id="0tfdn1"
queue_dead_letter_count
history_moved_to_dead_letter_count
```

Dead-letter visibility helps prevent silent data quality failures.

## Why History Metrics Matter

Queue history is the operational evidence trail.

It answers questions such as:

```text id="w5o5ac"
Was the item created?
Was it claimed?
Did it complete?
Did it fail?
Was a retry scheduled?
Was it moved to dead-letter?
```

This feature captures history action counts so the queue state can be compared against the evidence trail.

## Assertions Validated

Expected assertions:

```text id="e1d93a"
queue_total_count_assertion | passed
queue_status_distribution_assertion | passed
queue_retry_pressure_assertion | passed
queue_dead_letter_assertion | passed
queue_age_metrics_assertion | passed
queue_processing_age_metrics_assertion | passed
queue_history_metrics_assertion | passed
ROLLBACK
```

These assertions validate that the queue metrics baseline is complete and repeatable.

## Why ROLLBACK Is Used

The validation runs inside a transaction and ends with:

```sql id="jgbnz2"
ROLLBACK;
```

This is intentional.

The script creates synthetic review items, synthetic queue items, and synthetic queue history records.

Rollback removes that data after validation, keeping the script safe to run repeatedly in local and automated environments.

## What This Feature Does Not Do

This feature does not:

```text id="3e4y50"
run a load test
measure maximum throughput
simulate concurrent workers
benchmark cloud queue infrastructure
prove production-scale performance
tune queue indexes
change queue behavior
```

It establishes a queue health metrics baseline.

Throughput, concurrency, and tuning can come later.

## Manual Validation

Run:

```powershell id="ext1gt"
Get-Content scripts\validate_queue_performance_metrics_baseline.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected assertions:

```text id="eig7zo"
queue_total_count_assertion | passed
queue_status_distribution_assertion | passed
queue_retry_pressure_assertion | passed
queue_dead_letter_assertion | passed
queue_age_metrics_assertion | passed
queue_processing_age_metrics_assertion | passed
queue_history_metrics_assertion | passed
ROLLBACK
```

## Automated Validation

Run the focused queue metrics baseline test:

```powershell id="wn75xb"
python -m pytest tests/integration/test_queue_performance_metrics_baseline.py -v
```

Run the queue reliability group:

```powershell id="dfu1mt"
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py tests/integration/test_queue_performance_metrics_baseline.py -v
```

Run the full reliability and performance validation group:

```powershell id="afurxo"
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py tests/integration/test_query_performance_baseline.py tests/integration/test_query_performance_tuning_comparison.py tests/integration/test_api_endpoint_performance_baseline.py tests/integration/test_queue_performance_metrics_baseline.py -v
```

## Example Metric Output

A successful run reports metrics similar to:

```text id="rqwmav"
queue_total_count | 30
queue_ready_count | 10
queue_processing_count | 5
queue_completed_count | 7
queue_failed_count | 4
queue_dead_letter_count | 4
queue_retry_eligible_count | 4
queue_max_attempt_count | 3
oldest_ready_item_age_minutes | ...
oldest_processing_item_age_minutes | ...
history_created_count | 30
history_claimed_count | 20
history_completed_count | 7
history_failed_count | 8
history_retry_scheduled_count | 4
history_moved_to_dead_letter_count | 4
```

## Operational Interpretation

A queue metrics baseline is useful because it gives support and reliability teams concrete signals to watch.

Examples:

```text id="91fp3r"
Ready count rising may indicate workers are not keeping up.
Oldest ready item age rising may indicate backlog risk.
Processing count stuck may indicate locked or hung work.
Failed count rising may indicate downstream instability.
Retry-eligible count rising may indicate repeated transient failures.
Dead-letter count rising may indicate poison messages or data defects.
History counts help verify the evidence trail.
```

The local validation does not treat these as production failure thresholds.

It identifies which metrics should be visible and testable.

## Production Monitoring Candidates

In a production-like environment, these queue metrics could support alerts and dashboards:

```text id="mynckj"
ready queue depth
oldest ready item age
processing queue depth
oldest processing item age
failed count
retry-eligible count
dead-letter count
retry rate
dead-letter rate
worker claim rate
worker completion rate
worker failure rate
queue age distribution
```

A useful operational interpretation is:

```text id="se6u1i"
This metric was not a failure condition in the local validation environment, but it is a production monitoring candidate under higher concurrency or larger data volume.
```

## Reliability Value

This feature demonstrates:

```text id="tdchzp"
queue health metrics baseline discipline
deterministic synthetic queue state
status distribution validation
retry pressure visibility
dead-letter visibility
backlog age visibility
processing lock age visibility
history evidence validation
rollback-safe repeatability
separation between health metrics and throughput testing
```

This is relevant to Software Development Engineer in Test (SDET), Site Reliability Engineering (SRE), application support, production support, healthcare integration testing, and database-backed reliability validation roles.

## Scope

This feature uses synthetic healthcare-style data only.

It does not use real patient data, protected health information, production credentials, or production database exports.

It does not claim production-scale queue performance results.

It establishes a repeatable local queue health metrics baseline for future comparison.

## Summary

Queue Performance Metrics Baseline adds operational visibility into the background work queue.

It captures queue depth, status distribution, retry pressure, dead-letter count, backlog age, processing age, and history action evidence.

This feature strengthens the project by connecting API and database performance work to background queue health, which is a major part of modern reliability engineering.
