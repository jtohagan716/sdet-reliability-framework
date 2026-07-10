# Query Performance Tuning Comparison

## Purpose

The Query Performance Tuning Comparison feature demonstrates a controlled pre/post performance tuning workflow for the healthcare data quality query introduced in the Query Performance Baseline Validation feature.

The goal is not to make broad production performance claims.

The goal is to prove a disciplined tuning process:

```text
capture pre-tuning evidence
apply one targeted change
capture post-tuning evidence
compare the results
preserve expected behavior
interpret the outcome honestly
rollback the validation data and tuning change
```

This feature extends the project’s performance specialization path by moving from baseline-only measurement to measured tuning comparison.

## Why This Matters

Performance tuning should be evidence-based.

A tuning change should not be applied simply because an index seems useful.

A responsible workflow asks:

```text
What is the query doing before the change?
What access path is PostgreSQL using?
What tuning change is being applied?
Does the post-change plan actually use the tuning change?
Did the query still return the correct results?
Did the tuning change reduce work?
What are the limitations of the measurement?
```

This feature answers those questions with repeatable SQL validation and automated pytest coverage.

## Scenario

The validation models a healthcare data quality support workflow.

A reviewer or operational support user needs to retrieve:

```text
pending high-priority patient data quality review items
patient reference
encounter reference
assigned role
related queue work item
queue status
attempt count
maximum attempts
```

The query answers:

```text
Which high-priority patient data quality review items are pending, and what is the related background queue state?
```

## Synthetic Dataset

The validation script creates a larger synthetic dataset than the baseline feature.

It creates:

```text
10,000 patient data quality review items
10,000 matching data quality work queue items
100 high-priority pending review items
80 ready queue items
20 processing queue items
9,900 completed queue items
```

The query returns the first 25 pending high-priority review items ordered by creation time and review item key.

## Tables Used

The validation uses:

```text
patient_data_quality_review_items
data_quality_work_queue
```

The join condition is:

```text
data_quality_work_queue.source_review_item_key = patient_data_quality_review_items.review_item_key
```

## Query Shape

The query filters by:

```text
review_status = 'pending_review'
review_priority = 'high'
```

It orders by:

```text
created_at
review_item_key
```

It limits the result set:

```text
LIMIT 25
```

This query shape is important because the tuning change is intended to support the filter, ordering, and limit pattern.

## Pre-Tuning Plan

Before the tuning change, PostgreSQL used the existing separate indexes on review status and review priority.

The observed pre-tuning plan included:

```text
Bitmap Heap Scan on patient_data_quality_review_items
BitmapAnd
Bitmap Index Scan on idx_patient_data_quality_review_items_review_priority
Bitmap Index Scan on idx_patient_data_quality_review_items_review_status
Nested Loop Left Join
Index Scan on data_quality_work_queue.source_review_item_key
Sort
```

This shows that PostgreSQL was already using available indexes.

The pre-tuning plan was not “bad” in a simple sense.

However, it still had to combine separate indexes, retrieve the target rows, sort them, and then apply the limit.

## Targeted Tuning Change

The validation applies one targeted composite index:

```text
idx_perf_tuning_review_status_priority_created_key
```

The index columns are:

```text
review_status
review_priority
created_at
review_item_key
```

This index supports the query’s:

```text
status filter
priority filter
created_at ordering
review_item_key ordering
LIMIT behavior
```

The index is created inside the validation transaction and rolled back at the end.

It is not permanently added to the database by this validation script.

## Post-Tuning Plan

After the composite index is created, PostgreSQL uses:

```text
Index Scan using idx_perf_tuning_review_status_priority_created_key
```

This is the key tuning evidence.

The post-tuning plan shows that the targeted index supports the filtered, ordered, limited query shape.

Because the index matches the query pattern, PostgreSQL can satisfy the `LIMIT 25` earlier and avoid some of the extra work seen in the pre-tuning plan.

## Observed Pre/Post Metrics

One observed manual validation run produced the following local metrics:

```text
Metric              Pre-tuning        Post-tuning
Planning Time       20.927 ms         19.939 ms
Execution Time      66.748 ms         0.276 ms
Buffer Activity     shared hit=311    shared hit=77 read=2
Result Rows         25 returned       25 returned
Target Dataset      100 rows          100 rows
Queue Links         100 linked        100 linked
```

## Pre/Post Interpretation

The post-tuning query used the targeted composite index.

The observed local execution time improved substantially in the manual validation run.

The buffer activity was also reduced, although the post-tuning run included two reads because the new index had just been created inside the transaction.

The result set remained correct.

The queue linkage remained correct.

The tuning change improved the access path without changing expected functional behavior.

## Why This Is Not a Production Benchmark

This validation uses a local Docker-based PostgreSQL environment and synthetic data.

The observed improvement is useful evidence, but it should not be presented as a production-scale benchmark.

Local timing can be affected by:

```text
Docker Desktop resource state
host machine load
cache warm-up
PostgreSQL planner state
newly created index pages
small synthetic dataset behavior
CI environment differences
```

The correct professional interpretation is:

```text
In this local synthetic validation, the targeted composite index changed the query plan and reduced observed execution time. The result is useful as access-path evidence, but production-scale validation would require production-like data volume, concurrency, workload mix, and monitoring.
```

## Assertions Validated

The validation checks:

```text
tuning_result_row_count_assertion
tuning_target_dataset_assertion
tuning_queue_linkage_assertion
tuning_index_created_assertion
pre_post_report_ready_assertion
```

Expected result:

```text
tuning_result_row_count_assertion | passed
tuning_target_dataset_assertion | passed
tuning_queue_linkage_assertion | passed
tuning_index_created_assertion | passed
pre_post_report_ready_assertion | passed
ROLLBACK
```

## Why ROLLBACK Is Used

The validation ends with:

```sql
ROLLBACK;
```

This is intentional.

The script creates:

```text
10,000 review items
10,000 queue items
temporary tuning index
```

The transaction rollback removes the synthetic data and the tuning index so the validation remains repeatable and deterministic.

This keeps the test safe for repeated local and automated runs.

## Test Design Note

The baseline performance test was updated during this work to avoid brittle assumptions about a single exact PostgreSQL join strategy.

PostgreSQL may choose different valid plan shapes depending on statistics, indexes, data volume, cache state, and cost estimates.

The baseline test now validates that plan evidence exists without requiring one exact join type.

The tuning comparison test is more specific because it intentionally validates that the targeted composite index is created and used.

This distinction is important:

```text
Baseline test: prove measurement evidence exists.
Tuning comparison test: prove the targeted tuning behavior occurs.
```

## Manual Validation

Run:

```powershell
Get-Content scripts\validate_query_performance_tuning_comparison.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected assertions:

```text
tuning_result_row_count_assertion | passed
tuning_target_dataset_assertion | passed
tuning_queue_linkage_assertion | passed
tuning_index_created_assertion | passed
pre_post_report_ready_assertion | passed
ROLLBACK
```

## Automated Validation

Run the focused tuning comparison test:

```powershell
python -m pytest tests/integration/test_query_performance_tuning_comparison.py -v
```

Run the performance validation pair:

```powershell
python -m pytest tests/integration/test_query_performance_baseline.py tests/integration/test_query_performance_tuning_comparison.py -v
```

Run the queue reliability and performance validation group:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py tests/integration/test_query_performance_baseline.py tests/integration/test_query_performance_tuning_comparison.py -v
```

## Reliability and Performance Value

This feature demonstrates:

```text
pre-tuning query plan capture
post-tuning query plan capture
targeted composite index validation
index usage verification
planning and execution timing capture
buffer evidence capture
result correctness preservation
queue linkage preservation
rollback-safe repeatability
avoidance of brittle timing assertions
honest pre/post performance interpretation
```

This is relevant to Software Development Engineer in Test (SDET), Site Reliability Engineering (SRE), application support, production support, healthcare integration testing, and database-backed reliability validation roles.

## Future Enhancements

Future performance work can extend this feature by adding:

```text
larger synthetic data volumes
multiple repeated timing runs
average/min/max timing summaries
pre/post metric table generation
API endpoint timing comparison
Prometheus metrics
Grafana dashboard panels
OpenTelemetry trace correlation
queue depth and queue age metrics
container CPU and memory observations
production risk indicator reporting
```

## Production Monitoring Candidates

This local validation does not prove production behavior.

However, it identifies useful production monitoring candidates:

```text
query execution time
query planning time
buffer reads
buffer hits
rows scanned
rows returned
queue depth
oldest ready queue item age
retry count
dead-letter count
API p95 latency
API p99 latency
database lock waits
container CPU pressure
container memory pressure
context switching where available
```

A useful operational interpretation is:

```text
This metric was not a failure condition in the local validation environment, but it is a production monitoring candidate under higher concurrency or larger data volume.
```

## Scope

This feature uses synthetic healthcare-style data only.

It does not use real patient data, protected health information, production credentials, or production database exports.

It does not claim production-scale performance results, production tuning recommendations, or database administrator-level tuning.

It demonstrates a controlled local pre/post tuning comparison workflow.

## Summary

Query Performance Tuning Comparison demonstrates an evidence-based tuning workflow.

It captures pre-tuning behavior, applies one targeted composite index, captures post-tuning behavior, validates that the index is used, confirms result correctness, and rolls back the synthetic data and tuning change.

This feature strengthens the project’s performance specialization path by showing disciplined measurement, targeted tuning, and honest interpretation.
