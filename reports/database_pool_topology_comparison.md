# Database Pool Topology Comparison

## Study design

- Repeated measured runs per topology: 3
- Combined connection budget: minimum 4, maximum 8
- Foreground requests per run: 60
- Foreground concurrency: 6
- Foreground connection hold: 100 ms
- Background requests per run: 20
- Background concurrency: 4
- Background batch size: 2

## Runtime-verified pool budgets

| Topology | Physical pools | Foreground max | Background max | Combined max |
|---|---:|---:|---:|---:|
| Shared pool | 1 | 8 | 8 | 8 |
| Isolated pools | 2 | 6 | 2 | 8 |

The shared foreground and background values refer to the same physical pool and are counted once in the combined budget.

## Three-run averages

| Metric | Shared pool | Isolated pools | Isolated vs. shared |
|---|---:|---:|---:|
| Elapsed seconds | 1.263 | 1.373 | +8.709% |
| Foreground p50 ms | 114.199 | 123.993 | +8.576% |
| Foreground p95 ms | 158.698 | 172.117 | +8.456% |
| Foreground acquire p95 ms | 11.936 | 0.151 | -98.735% |
| Foreground later-request average ms | 116.529 | 125.731 | +7.897% |
| Background p95 ms | 88.738 | 114.189 | +28.681% |
| Trials with observed foreground waiting | 3 | 0 | — |

## Per-run measurements

| Topology | Run ID | Foreground p50 ms | Foreground p95 ms | Acquire p95 ms | Background p95 ms | Foreground waiting peak |
|---|---|---:|---:|---:|---:|---:|
| `shared_pool` | `foreground-background-shared-pool-20260730T204616076911Z` | 113.440 | 149.747 | 14.594 | 84.589 | 1 |
| `shared_pool` | `foreground-background-shared-pool-20260730T204620139550Z` | 119.837 | 172.906 | 6.658 | 86.455 | 1 |
| `shared_pool` | `foreground-background-shared-pool-20260730T204624455404Z` | 109.321 | 153.440 | 14.555 | 95.169 | 1 |
| `isolated_pools` | `foreground-background-isolated-pools-20260730T204340930176Z` | 122.591 | 150.030 | 0.289 | 81.736 | 0 |
| `isolated_pools` | `foreground-background-isolated-pools-20260730T204345191440Z` | 135.026 | 201.201 | 0.093 | 165.868 | 0 |
| `isolated_pools` | `foreground-background-isolated-pools-20260730T204349668017Z` | 114.361 | 165.121 | 0.070 | 94.963 | 0 |

## Interpretation

With the same runtime-verified maximum budget of 8 PostgreSQL connections, isolated pools reduced average foreground acquisition p95 by 98.735%.
Observed foreground waiting occurred in 3 of 3 shared-pool trials and 0 of 3 isolated-pool trials.
The isolation benefit did not produce a lower average end-to-end foreground p95 under this workload.

The evidence supports a workload-isolation conclusion, not a general claim that isolated pools always improve overall response time.

## Limitations

- The study used a local Windows and Docker environment.
- Each topology was measured in three formal runs.
- The workload was synthetic and intentionally controlled.
- Pool waiting counters are sampled runtime observations.
- Results should not be generalized to unrelated workloads.

## Source runs

### Shared pool

- `foreground-background-shared-pool-20260730T204616076911Z`
- `foreground-background-shared-pool-20260730T204620139550Z`
- `foreground-background-shared-pool-20260730T204624455404Z`

### Isolated pools

- `foreground-background-isolated-pools-20260730T204340930176Z`
- `foreground-background-isolated-pools-20260730T204345191440Z`
- `foreground-background-isolated-pools-20260730T204349668017Z`
