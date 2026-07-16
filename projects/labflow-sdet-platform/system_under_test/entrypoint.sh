#!/bin/sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

echo "Starting LabFlow API..."
exec uvicorn system_under_test.api.main:app \
  --host "${APP_HOST:-0.0.0.0}" \
  --port "${APP_PORT:-8000}"
