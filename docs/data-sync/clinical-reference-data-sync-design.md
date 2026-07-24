# Clinical Reference Data Synchronization Design

## Purpose

This workstream demonstrates the validation, reliability, and performance engineering required to synchronize healthcare reference data from an authoritative central repository to a downstream facility cache.

The project models a generic distributed healthcare system using synthetic data. It does not reproduce any proprietary system or contain real patient information.

The synchronization process must satisfy two equally important requirements:

1. Deliver complete and accurate reference data.
2. Complete within a restricted overnight processing window before the next business day.

A synchronization run that finishes with incorrect data is a failure. A correct synchronization run that finishes after the operational deadline is also a failure.

## Business Scenario

Healthcare facilities depend on locally available reference data for clinical and administrative workflows.

An authoritative central repository maintains reference values such as appointment types, provider specialties, clinical statuses, and facility identifiers. During off-hours, a scheduled synchronization process updates a facility cache from the central repository.

The facility cache must be ready before normal business operations begin.

The synchronization process must provide enough evidence to answer:

* Did every eligible source record reach the facility cache?
* Were changed records updated correctly?
* Were obsolete records handled according to the business rules?
* Were invalid or duplicate records rejected safely?
* Was the synchronization completed atomically?
* Can a failed run be restarted without duplicating work?
* Did the run complete within the approved processing window?
* Did the batch workload adversely affect foreground application traffic?

## Initial Architecture

```text
┌──────────────────────────────┐
│ Central Clinical Repository  │
│                              │
│ Authoritative reference data │
└──────────────┬───────────────┘
               │
               │ scheduled synchronization
               ▼
┌──────────────────────────────┐
│ Synchronization Process      │
│                              │
│ validation                   │
│ transformation               │
│ loading                      │
│ auditing                     │
│ reconciliation               │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Facility Cache               │
│                              │
│ Locally available reference  │
│ data for operational use     │
└──────────────────────────────┘

               │
               ▼
┌──────────────────────────────┐
│ Synchronization Control      │
│                              │
│ run status                   │
│ row counts                   │
│ rejected records             │
│ checkpoints                  │
│ performance evidence         │
└──────────────────────────────┘
```

The initial implementation will use one PostgreSQL instance with three schemas:

* `central_repository`
* `facility_cache`
* `sync_control`

Using separate schemas provides clear ownership boundaries while keeping the first implementation understandable and reproducible.

A later phase may place the central repository and facility cache in separate PostgreSQL containers to introduce network, connection, and distributed-failure behavior.

## Component Responsibilities

### Central Repository

The `central_repository` schema represents the authoritative data source.

It is responsible for storing:

* Business keys
* Reference codes
* Display values
* Active and inactive status
* Effective and expiration dates
* Source update timestamps
* Source version information

The synchronization process must not modify authoritative source records.

### Facility Cache

The `facility_cache` schema represents the downstream operational copy.

It is responsible for storing:

* Synchronized business values
* Source version information
* Synchronization run identifier
* Last synchronization timestamp

The facility cache must contain only records that comply with the documented source-to-target rules.

### Synchronization Control

The `sync_control` schema stores operational evidence.

It will eventually include:

* Synchronization run identifier
* Load mode
* Start and completion timestamps
* Run status
* Source row count
* Inserted row count
* Updated row count
* Deactivated or removed row count
* Rejected row count
* Target row count
* Reconciliation result
* Processing-window result
* Error details
* Incremental-load checkpoint

A run may be marked successful only after loading and reconciliation both succeed.

## Initial Reference Domain

The first implementation will use an appointment-type reference table.

Example business values may include:

* Routine visit
* Follow-up visit
* Urgent visit
* Procedure
* Telehealth visit

All data will be synthetic.

The initial source record will contain:

| Field                   | Purpose                                       |
| ----------------------- | --------------------------------------------- |
| `appointment_type_code` | Stable business key                           |
| `display_name`          | User-facing value                             |
| `description`           | Additional reference information              |
| `active_flag`           | Whether the value remains operationally valid |
| `effective_date`        | First valid business date                     |
| `expiration_date`       | Optional final valid business date            |
| `source_updated_at`     | Authoritative update timestamp                |
| `source_version`        | Monotonically increasing source version       |

The facility-cache record will preserve the business values and add:

| Field         | Purpose                                        |
| ------------- | ---------------------------------------------- |
| `sync_run_id` | Run responsible for the current cached version |
| `synced_at`   | Time the record was written to the cache       |

## Synchronization Modes

### Full Refresh

A full refresh processes every eligible source record.

The logical full-refresh behavior is:

1. Start a synchronization run.
2. Validate the source dataset.
3. Reject the run if blocking source defects exist.
4. Load the complete eligible dataset into the facility cache.
5. Remove or replace obsolete cached values according to the selected refresh strategy.
6. Reconcile source and target contents.
7. Mark the run successful only when reconciliation passes.

The first implementation will emphasize correctness and transactional safety. Alternative full-refresh strategies will be evaluated later during performance optimization.

### Incremental Synchronization

Incremental synchronization will be added after full-refresh correctness is proven.

It will process:

* Newly created records
* Changed records
* Deactivated records
* Late-arriving changes

A checkpoint may advance only after a successful and reconciled run.

Reprocessing the same source changes must not create duplicate records or repeat completed updates.

## Business Rules

1. The central repository is authoritative.

2. Every appointment type must have a nonblank business key.

3. The appointment-type business key must be unique within the source dataset.

4. Every active source record that is eligible on the processing date must appear in the facility cache.

5. Cached business values must match the documented source-to-target transformations.

6. An expiration date, when present, cannot precede the effective date.

7. Invalid source records must not silently enter the facility cache.

8. Rejected records must include a reason that identifies the failed rule.

9. A run with blocking source defects must not be marked successful.

10. A failed run must not leave a partially loaded cache represented as valid.

11. Synchronization audit totals must reconcile with the actual source and target changes.

12. Repeating the same input must not create duplicate data or duplicate change effects.

13. A checkpoint must not advance after a failed run.

14. A successful run must finish within the approved processing window.

15. Correctness validation must be repeated after every performance optimization.

## Initial Data-Quality Risks

### Missing Records

An eligible source record may fail to appear in the facility cache.

Potential impact:

* Users may be unable to select a valid reference value.
* Downstream records may be assigned an incorrect or outdated code.

### Unexpected Records

The facility cache may contain a record that is no longer present or eligible in the authoritative source.

Potential impact:

* Users may continue selecting an obsolete value.
* Different facilities may operate with inconsistent reference data.

### Duplicate Business Keys

The source or cache may contain multiple records for one business key.

Potential impact:

* Synchronization results become nondeterministic.
* Downstream lookups may return inconsistent values.

### Field-Level Mismatch

A cached record may exist but contain an incorrect display value, status, date, or version.

Potential impact:

* Row-count reconciliation may pass while the actual data remains wrong.

### Partial Load

The job may fail after loading only part of the source dataset.

Potential impact:

* The cache may appear available but contain an internally inconsistent reference set.

### Incorrect Success Status

The job may report success despite rejected records, incomplete loading, or failed reconciliation.

Potential impact:

* Operations personnel may not investigate a bad synchronization.
* Incorrect data may remain in use through the next business day.

### Unsafe Retry

A restarted job may duplicate records or reapply already completed changes.

Potential impact:

* Data corruption
* Inflated audit counts
* Extended recovery time

### Processing-Window Overrun

The synchronization may remain correct but finish after normal operations begin.

Potential impact:

* Facilities begin the day with stale data.
* Batch activity competes with foreground application traffic.
* There is insufficient time to diagnose and retry a failed run.

## Performance Requirement

The production-style requirement is expressed as a restricted processing window rather than an arbitrary speed target.

The synchronization must:

* Begin during the approved off-hours period.
* Finish before the next operational day.
* Preserve enough recovery margin for investigation or retry.
* Avoid unacceptable degradation of foreground application traffic.

Local development benchmarks will use scaled durations suitable for a workstation while preserving the same operational measurements:

* Total run duration
* Percentage of processing window consumed
* Remaining recovery margin
* Rows processed per second
* Phase duration
* Foreground latency during batch activity
* Correctness status after completion

Performance optimization will begin only after the correctness, reconciliation, restart, and idempotency requirements are automated.

## Validation Strategy

Validation will be developed in layers.

### Manual SQL Validation

Initial SQL will verify:

* Source row counts
* Target row counts
* Missing target records
* Unexpected target records
* Duplicate business keys
* Required values
* Invalid date ranges
* Field-level mismatches
* Audit-total reconciliation

### Automated Integration Validation

Docker-backed pytest integration tests will:

* Apply the synchronization schema explicitly.
* Execute validation SQL through PostgreSQL.
* Stop immediately on SQL errors.
* Skip cleanly when Docker or PostgreSQL is unavailable.
* Preserve useful standard output and standard error on failure.
* Roll back controlled validation data where appropriate.

### Performance Validation

Later performance tests will use:

* Deterministic dataset generation
* Fixed workload definitions
* Repeated trials
* Median results
* Phase-level timing
* PostgreSQL execution-plan evidence
* Controlled one-variable-at-a-time optimization
* Full correctness regression after each change

## First Milestone Scope

The first milestone includes:

* This design document
* Three PostgreSQL schemas
* One central appointment-type reference table
* One facility-cache appointment-type table
* Synchronization run and table-result control tables
* A small deterministic synthetic dataset
* Manual full-refresh SQL
* Manual source-to-target reconciliation
* One Docker-backed integration test

The first milestone does not include:

* Incremental synchronization
* Python synchronization services
* Pandas
* SQLAlchemy
* Multiple database containers
* Concurrency
* Performance optimization
* Dashboard development
* Foreground workload competition

Those capabilities will be introduced only after the first full-refresh behavior is proven and understood.

## First Milestone Acceptance Criteria

The milestone is complete when:

1. The database objects can be created repeatedly without errors.

2. A deterministic source dataset can be loaded.

3. A full refresh copies every eligible source record to the facility cache.

4. Source and target row counts reconcile.

5. No eligible source record is missing from the cache.

6. No unexpected target record remains after the refresh.

7. No duplicate business key exists in the source or target.

8. All synchronized business values match.

9. Synchronization audit totals match the actual data changes.

10. The validation executes through Docker Compose and PostgreSQL.

11. The integration test stops on any SQL error.

12. Validation data can be rolled back or reset reproducibly.

13. The test passes repeatedly from the same known starting state.

## Evidence Produced

The first milestone will produce:

* Architecture and requirements documentation
* PostgreSQL schema definition
* Deterministic source dataset
* Full-refresh SQL
* Source-to-target reconciliation output
* Automated integration-test result
* Git history showing controlled implementation steps

Later milestones will add:

* Incremental-load evidence
* Failure and recovery evidence
* Defect reports
* Performance baselines
* PostgreSQL execution plans
* Optimization comparisons
* Processing-window compliance reports
* Observability dashboards
* Release-readiness conclusions

## Design Principle

The project will preserve a strict evidence chain:

```text
Documented requirement
        ↓
Known test data
        ↓
Executed synchronization behavior
        ↓
Observed database state
        ↓
Automated reconciliation
        ↓
Recorded conclusion
```

Configuration, job labels, or exit codes alone are not proof of synchronization correctness. The final conclusion must be supported by observed source data, target data, audit records, and reproducible validation.
