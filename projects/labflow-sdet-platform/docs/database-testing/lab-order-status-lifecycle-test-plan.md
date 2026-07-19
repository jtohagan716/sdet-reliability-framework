# Lab Order Status Lifecycle: Database Test Plan

## 1. Purpose

This study verifies the correctness, transactional integrity, concurrency behavior,
and performance characteristics of the LabFlow lab-order status lifecycle.

The work is designed to demonstrate an independent database-testing capability
covering:

- requirements analysis;
- PostgreSQL functions and procedures;
- trigger and audit validation;
- direct database contract testing;
- deterministic test-data generation;
- concurrent workload generation;
- execution-plan analysis;
- performance baselining;
- evidence-based tuning;
- regression and release evaluation.

## 2. Current System State

At the start of this study:

- `public.lab_orders` stores lab orders.
- The PostgreSQL enum `lab_order_status` contains only `PLACED`.
- Newly created orders default to `PLACED`.
- No status-transition function exists.
- No controlled status-change procedure exists.
- No status-audit table or trigger exists.
- No API status-update operation exists.

The lifecycle will therefore be introduced incrementally, with tests written
against explicit requirements.

## 3. Proposed Status Lifecycle

The initial lifecycle contains four statuses:

- `PLACED`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`

### Allowed transitions

| Current status | Requested status | Expected result |
|---|---|---|
| PLACED | IN_PROGRESS | Allowed |
| PLACED | CANCELLED | Allowed |
| IN_PROGRESS | COMPLETED | Allowed |
| IN_PROGRESS | CANCELLED | Allowed |

### Rejected transitions

| Current status | Requested status | Expected result |
|---|---|---|
| PLACED | COMPLETED | Rejected |
| COMPLETED | PLACED | Rejected |
| COMPLETED | IN_PROGRESS | Rejected |
| COMPLETED | CANCELLED | Rejected |
| CANCELLED | PLACED | Rejected |
| CANCELLED | IN_PROGRESS | Rejected |
| CANCELLED | COMPLETED | Rejected |

`COMPLETED` and `CANCELLED` are terminal states.

A request to assign the current status again must not create a new audit event.

## 4. Database Objects Under Test

The study is expected to introduce and test:

1. Expanded PostgreSQL enum `lab_order_status`
2. Status-transition validation function
3. Controlled status-transition procedure or function
4. Status-audit table
5. Status-audit trigger function
6. Status-change trigger
7. Supporting indexes
8. Database roles or permissions where appropriate

The implementation may evolve as testing exposes design weaknesses.

## 5. Audit Requirements

A successful status change must create exactly one audit row containing:

- unique audit identifier;
- lab-order identifier;
- previous status;
- new status;
- change timestamp;
- changed-by identifier;
- change source.

The audit record must be created in the same transaction as the business change.

A rolled-back status update must leave:

- the original lab-order status unchanged;
- no committed audit record.

Updates that do not change the status must not create audit rows.

## 6. Functional Test Coverage

### 6.1 Enum and schema contracts

- All required statuses exist.
- Existing `PLACED` data remains valid after migration.
- Invalid enum values are rejected.
- Migration upgrade succeeds.
- Migration downgrade behavior is documented and tested where safe.

### 6.2 Transition validation

- Every allowed transition succeeds.
- Every rejected transition fails.
- Terminal states cannot transition.
- Null current status is handled deliberately.
- Null requested status is rejected.
- Unsupported status values are rejected by the database.
- Repeated inputs produce deterministic outcomes.

### 6.3 Audit behavior

- One actual status change creates exactly one audit row.
- Audit old status is correct.
- Audit new status is correct.
- Audit lab-order identifier is correct.
- Audit timestamp is populated.
- Audit metadata is correct.
- Same-status updates create no audit row.
- Unrelated column updates create no audit row.
- Multi-row updates create the expected number of audit rows.
- Failed updates create no orphan audit rows.

### 6.4 Transaction behavior

- Commit persists both status and audit.
- Rollback removes both status and audit.
- Validation failure leaves the transaction in a known state.
- Procedure failure does not partially update data.
- Savepoint behavior is tested where relevant.

### 6.5 Error handling

Tests will verify:

- PostgreSQL error type;
- SQLSTATE where useful;
- constraint or object name;
- error message stability only when appropriate;
- absence of unintended side effects.

## 7. Concurrency Risks

The study will investigate:

- two sessions updating the same order;
- competing valid transitions;
- competing valid and invalid transitions;
- lost-update risk;
- row-lock behavior;
- lock-wait duration;
- lock timeout behavior;
- deadlock risk;
- final status determinism;
- audit-history ordering;
- duplicate or misleading audit records.

Concurrency tests must use controlled coordination rather than relying only on
unpredictable timing.

## 8. Performance Risks

Potential risks include:

- row-level trigger overhead;
- audit-table growth;
- excessive index-maintenance cost;
- slow audit-history retrieval;
- contention on frequently updated orders;
- long-running transactions;
- poor cardinality estimates;
- sequential scans as data volume grows;
- sort or hash operations spilling to disk;
- connection saturation;
- increased write-ahead log volume;
- vacuum and table-bloat effects.

## 9. Dataset Strategy

Three deterministic dataset profiles will be supported.

### Small

Used for functional diagnosis and manual inspection.

- tens of patients;
- tens of encounters;
- hundreds of lab orders;
- limited audit history.

### Medium

Used for test development and initial plan analysis.

- thousands of patients;
- tens of thousands of encounters;
- hundreds of thousands of lab orders;
- one million or more audit rows.

### Large

Used for meaningful performance comparisons.

- scale determined by available workstation resources;
- millions of lab orders;
- tens of millions of audit rows where practical.

Each dataset must record:

- generator version;
- schema revision;
- scale profile;
- random seed;
- requested row counts;
- actual row counts;
- generation start and completion times.

## 10. Workload Types

The workload tooling will support:

- direct single-operation execution;
- sequential batch execution;
- fixed-concurrency execution;
- sustained-duration execution;
- read-heavy workloads;
- write-heavy workloads;
- mixed read/write workloads;
- direct function or procedure calls;
- audit-history retrieval;
- reporting and aggregation queries.

The workload generator must not depend on an application developer providing a
client.

## 11. Performance Measurements

Measurements will include, where applicable:

- operation count;
- success and failure count;
- throughput;
- minimum latency;
- mean latency;
- median latency;
- 95th percentile latency;
- 99th percentile latency;
- maximum latency;
- connection-acquisition time;
- lock-wait time;
- database execution time;
- rows examined and returned;
- execution-plan estimates and actuals;
- shared-buffer hits;
- physical reads;
- temporary-file activity;
- CPU and memory utilization;
- table and index size;
- write-ahead log generation.

## 12. Execution-Plan Analysis

Queries will be evaluated using controlled combinations of:

- `EXPLAIN`
- `EXPLAIN ANALYZE`
- `EXPLAIN (ANALYZE, BUFFERS)`

Each analysis must answer:

1. What execution path did PostgreSQL choose?
2. Which operation performed most of the work?
3. Were estimated and actual row counts reasonably aligned?
4. Were more rows processed than returned?
5. Did the expected index participate?
6. Did sorting or hashing spill to temporary storage?
7. Was the result repeatable?
8. What controlled experiment should be performed next?

## 13. Tuning Method

Every tuning experiment will follow this process:

1. Define the performance question.
2. Establish a reproducible dataset.
3. Establish the baseline.
4. Capture plans and system evidence.
5. Form one explicit hypothesis.
6. Change one primary variable.
7. Repeat the identical workload.
8. compare results across repeated runs;
9. rerun functional and transactional regression tests;
10. document benefits, costs, limitations, and recommendation.

No tuning change will be described as successful based on one execution.

## 14. Planned Initial Performance Study

The first study will evaluate audit-history retrieval as audit volume increases.

Candidate comparisons may include:

- no dedicated audit-history index;
- index on `lab_order_id`;
- composite index on `(lab_order_id, changed_at)`;
- reversed composite column order;
- query and pagination alternatives.

The study will measure both:

- read-performance improvement;
- audit-write and storage cost.

## 15. Evidence and Repository Artifacts

The repository will contain:

- requirements and test plans;
- Alembic migrations;
- direct database tests;
- deterministic dataset generators;
- workload-generator source code;
- experiment configuration;
- representative execution plans;
- summarized benchmark results;
- findings and recommendations;
- CI quality-gate evidence.

Large raw datasets, transient logs, credentials, and uncontrolled generated output
will not be committed.

## 16. Release Criteria

The lifecycle increment is acceptable only when:

- all allowed transitions behave correctly;
- all invalid transitions are rejected;
- status and audit changes are atomic;
- audit records are complete and accurate;
- rollback behavior is verified;
- concurrency behavior is documented;
- existing API and database regression tests pass;
- migrations pass automated validation;
- performance findings are based on repeatable evidence;
- identified tradeoffs are documented.

## 17. Transferable Skills

Although PostgreSQL is the implementation platform, the study emphasizes concepts
that transfer to other production databases:

- transactional atomicity;
- stored-program validation;
- trigger testing;
- locking and concurrency;
- execution-plan interpretation;
- cardinality estimation;
- index design;
- query tuning;
- connection management;
- workload modeling;
- performance regression testing;
- evidence-based change evaluation.
