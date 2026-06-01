#!/bin/bash
set -e

echo "==> [1/3] Checking environment..."
echo "    DATABASE_URL: ${DATABASE_URL:0:40}..."
echo "    REDIS_URL:    $REDIS_URL"

echo "==> [2/3] Running Alembic migrations..."
alembic upgrade head && echo "    Migrations OK" || { echo "    MIGRATION FAILED"; exit 1; }

echo "==> [3/3] Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
