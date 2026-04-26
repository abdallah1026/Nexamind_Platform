#!/bin/bash
set -e

echo "Initializing NexaMind Database..."

DB_URL="${DATABASE_URL:-postgresql://nexamind:nexamind_secret@localhost:5432/nexamind}"

# Wait for postgres
until pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-nexamind}"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready."

# Run migrations via alembic
cd /app && alembic upgrade head && echo "Migrations complete."
