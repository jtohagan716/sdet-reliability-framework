# LabFlow v0.1 Architecture

## Services

1. **API**
   - Python 3.12
   - FastAPI
   - SQLAlchemy
   - Alembic
   - Host port 8000

2. **PostgreSQL**
   - PostgreSQL 16
   - Container port 5432
   - Windows host port 5433

## Request flow

1. Client sends `POST /api/v1/lab-orders`.
2. FastAPI validates JSON using Pydantic.
3. The route calls `LabOrderService`.
4. The service checks the placer order number.
5. The repository writes through SQLAlchemy.
6. PostgreSQL enforces constraints.
7. The API returns HTTP 201.

## Test boundaries

- JSON request validation
- Duplicate placer order rule
- Database uniqueness enforcement
- API error contract
- API-to-database consistency
- Liveness versus readiness
