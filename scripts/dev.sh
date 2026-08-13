#!/usr/bin/env bash
# Single source of the local dev commands. Runs the FastAPI backend, the
# SvelteKit frontend, or (by default) both side by side.
#
# Usage: dev.sh [backend|frontend|all]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
TARGET="${1:-all}"

run_backend() {
	if [ ! -x "$ROOT_DIR/backend/.venv/bin/uvicorn" ]; then
		echo "Backend virtualenv not found. Run 'make install' first." >&2
		exit 1
	fi
	cd "$ROOT_DIR/backend" && exec .venv/bin/uvicorn app.main:app --reload --port "$BACKEND_PORT"
}

run_frontend() {
	if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
		echo "Frontend dependencies not found. Run 'make install' first." >&2
		exit 1
	fi
	cd "$ROOT_DIR/frontend" && exec npm run dev -- --port "$FRONTEND_PORT"
}

case "$TARGET" in
backend) run_backend ;;
frontend) run_frontend ;;
all) ;;
*)
	echo "Unknown target '$TARGET'. Use backend, frontend, or all." >&2
	exit 1
	;;
esac

pids=()

cleanup() {
	for pid in "${pids[@]}"; do
		kill "$pid" 2>/dev/null || true
	done
}

trap cleanup EXIT INT TERM

(run_backend) &
pids+=("$!")

(run_frontend) &
pids+=("$!")

wait
