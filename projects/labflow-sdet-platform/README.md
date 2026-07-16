# LabFlow v0.1 — System Under Test

LabFlow is a synthetic laboratory-order workflow used to practice modern SDET,
systems administration, database validation, reliability testing, and operational
diagnosis.

## Scope of v0.1

- FastAPI REST service
- PostgreSQL persistence
- Alembic database migration
- Laboratory-order creation and retrieval
- Liveness and readiness checks
- Docker Compose startup
- Operational PowerShell scripts
- Architecture, configuration, and database documentation

RabbitMQ, Redis, observability, browser UI, HL7, FHIR-shaped resources, fault
injection, and performance tooling will be added in later releases.

## Safety

All data must be synthetic. Do not use real patient data, credentials, or
Protected Health Information (PHI).

## Quick start

1. Copy `.env.example` to `.env`.
2. Review `.env`.
3. Run `docker compose up --build -d`.
4. Run `docker compose ps`.
5. Open `http://localhost:8000/docs`.
6. Follow `docs/first_day_runbook.md`.

The application is the test target. Your main engineering work will eventually
live under `automation/`.
