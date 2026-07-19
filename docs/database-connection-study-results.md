# Database Connection Strategy Study

## Test design

- Warm steady-state workload
- 200 requests per run
- 20 concurrent workers
- Three repetitions per configuration
- Zero request failures across all nine runs
- Median used for configuration comparisons

## Median results

| Configuration | Throughput | Client mean | Client p95 | Acquire mean | Acquire p95 | DB total mean | DB total p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| direct | 94.99 | 201.991 | 324.409 | 59.137 | 151.514 | 89.581 | 205.099 |
| dynamic-4-8 | 167.791 | 112.023 | 190.561 | 2.637 | 19.97 | 23.351 | 47.63 |
| fixed-8 | 180.398 | 104.892 | 159.142 | 2.796 | 15.828 | 24.178 | 55.86 |

## Pooled strategies relative to direct

### Dynamic 4-8

- Throughput gain: 76.641%
- Client p95 reduction: 41.259%
- Acquire p95 reduction: 86.82%
- Database-total p95 reduction: 76.777%

### Fixed 8

- Throughput gain: 89.913%
- Client p95 reduction: 50.944%
- Acquire p95 reduction: 89.553%
- Database-total p95 reduction: 72.764%

## Decision

Use the bounded connection pool for the application workload. Creating one physical PostgreSQL connection per operation was the dominant database cost under concurrency.

Retain a dynamic minimum of 4 and maximum of 8 as the project default. Fixed 8 did not demonstrate a clean database-latency advantage and permanently consumes four additional idle PostgreSQL sessions.

## Limitations

- Results apply to this local containerized workload and synthetic patient lookup.
- Host scheduling and container contention introduced visible run-to-run variation.
- The warm-up can grow the dynamic pool before the measured workload, so this study does not prove the optimal minimum pool size.
- Production pool sizing must also account for API replica count and the PostgreSQL connection budget.
