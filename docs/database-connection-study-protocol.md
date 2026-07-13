# Database Connection Study Test Protocol

## Purpose

This study compares database connection strategies under controlled,
repeatable workloads.

The principal comparison is:

- connection per operation
- bounded database connection pool

The study separately evaluates:

- cold-start behavior
- warm steady-state behavior
- interactive API traffic
- continuous queue-processing traffic
- shared versus workload-isolated connection capacity

## Starting-State Principle

Every measured run must begin with an explicitly recorded starting state.

Restarting services is one reset mechanism, but a restart alone does not
guarantee identical data, cache, connection, workload, or host conditions.

Each run must record:

- Git branch and commit
- connection strategy
- cold or warm run classification
- service readiness
- database validation result
- PostgreSQL session state
- warm-up policy
- stabilization interval
- workload parameters
- container state
- start time and run identifier

## Warm Steady-State Runs

Warm steady-state runs are the primary basis for comparing recurring
connection cost.

Preparation sequence:

1. Verify PostgreSQL readiness.
2. Verify API readiness.
3. Verify expected database records.
4. Verify there are no idle-in-transaction sessions.
5. Run the configured warm-up workload.
6. Discard all warm-up results.
7. Wait for the configured stabilization interval.
8. Recheck PostgreSQL session state.
9. Record the starting-state manifest.
10. Begin the measured workload.

Warm runs do not restart PostgreSQL or the API before every repetition.

## Cold-Start Runs

Cold-start runs evaluate deployment, restart, recovery, and first-use
behavior.

Preparation sequence:

1. Restart PostgreSQL.
2. Wait for PostgreSQL readiness.
3. Restart the API.
4. Wait for API readiness.
5. Verify expected database records.
6. Do not issue database warm-up traffic.
7. Record the starting-state manifest.
8. Begin the measured workload.

A container-restarted run is not described as a completely cold operating
system or filesystem-cache run.

## Workload Controls

Unless a scenario explicitly states otherwise, interactive workload runs use:

- 200 measured requests
- 20 concurrent workers
- 10 sequential requests per worker
- persistent HTTP session per worker
- unique request identifiers
- identical endpoint and patient identifier
- identical connect and read timeouts
- client-side CSV evidence
- server-side request correlation
- PostgreSQL connection observations

## Repetition Policy

Final comparisons require at least five measured repetitions for each
configuration.

Run order should alternate or be randomized rather than executing every
sample of one strategy before the other.

Example:

- A
- B
- B
- A
- A
- B
- B
- A
- A
- B

This reduces bias from host temperature, memory pressure, caching, Docker
Desktop behavior, and background operating-system activity.

## Validity Rules

A measured run is invalid when:

- PostgreSQL or the API is unhealthy
- expected database records are missing
- idle-in-transaction sessions exist before measurement
- workload parameters differ from the intended scenario
- the connection strategy cannot be identified
- another load generator is active
- warm-up results are accidentally included
- required evidence files are missing
- source or configuration changes during the run

Invalid runs remain available for investigation but are excluded from the
architecture comparison.

## Current Baseline

The current implementation uses one physical Psycopg connection per database
operation.

Warmed sequential observations show that physical connection establishment
is the dominant measured database phase, while query, fetch, and connection
close costs are substantially smaller.

Commit:

`c76d19f Add connection-per-operation timing baseline`
