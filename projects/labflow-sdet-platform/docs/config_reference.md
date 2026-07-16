# Configuration Reference

| Variable | Purpose | Example |
|---|---|---|
| `POSTGRES_DB` | Database name | `labflow` |
| `POSTGRES_USER` | Application database user | `labflow_app` |
| `POSTGRES_PASSWORD` | Local-only password | change locally |
| `POSTGRES_HOST` | Docker service hostname | `postgres` |
| `POSTGRES_PORT` | Internal PostgreSQL port | `5432` |
| `DATABASE_URL` | SQLAlchemy connection string | see `.env.example` |
| `APP_ENV` | Environment label | `local` |
| `APP_HOST` | API bind address | `0.0.0.0` |
| `APP_PORT` | API port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

PostgreSQL is exposed to Windows on host port `5433` to avoid conflicts with a
local PostgreSQL server using 5432.
