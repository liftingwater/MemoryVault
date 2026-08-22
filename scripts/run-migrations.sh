#!/usr/bin/env bash
# Run database migrations against Supabase
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIGRATIONS_DIR="${ROOT_DIR}/backend/migrations"

# Load environment variables
if [ -f "${ROOT_DIR}/backend/.env" ]; then
  set -a
  source "${ROOT_DIR}/backend/.env"
  set +a
fi

# Validate required env vars
if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "Error: SUPABASE_DB_URL not set. Run setup-supabase.sh first." >&2
  exit 1
fi

echo "Running migrations from ${MIGRATIONS_DIR}..."
echo "Database: $(echo ${SUPABASE_DB_URL} | sed 's/:[^:]*@/@/g')"

# Find all migration files in order and execute them
for migration in $(ls "${MIGRATIONS_DIR}"/*.sql | sort); do
  echo ""
  echo "--- Executing $(basename $migration)..."
  psql "${SUPABASE_DB_URL}" -f "$migration"
  echo "✓ Completed $(basename $migration)"
done

echo ""
echo "✅ All migrations completed successfully!"
