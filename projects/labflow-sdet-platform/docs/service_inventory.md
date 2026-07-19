# Service and Port Inventory

| Service | Container | Internal | Host | Purpose |
|---|---|---:|---:|---|
| FastAPI | `labflow-api` | 8000 | 8000 | REST API and OpenAPI |
| PostgreSQL | `labflow-postgres` | 5432 | 5433 | Transactional store |

Docker network: `labflow-network`

Persistent volume: `labflow_postgres_data`
