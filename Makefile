PYTHON_VERSION ?= 3.13
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
STACK_NAME ?= memoryvault
AWS_REGION ?= us-east-1
# ARTIFACTS_BUCKET must be set externally: make bootstrap creates it once.

# Auto-load .env if it exists. Command-line overrides still win.
-include .env
export

.PHONY: install install-backend install-frontend \
	dev dev-backend dev-frontend \
	test test-backend test-frontend \
	typecheck typecheck-backend typecheck-frontend \
	build clean \
	bootstrap deploy

install: install-backend install-frontend

install-backend:
	uv venv --python $(PYTHON_VERSION) backend/.venv
	cd backend && VIRTUAL_ENV=.venv uv pip install -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

dev:
	BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) ./scripts/dev.sh all

dev-backend:
	BACKEND_PORT=$(BACKEND_PORT) ./scripts/dev.sh backend

dev-frontend:
	FRONTEND_PORT=$(FRONTEND_PORT) ./scripts/dev.sh frontend

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/python -m pytest

test-frontend:
	cd frontend && npm run test

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd backend && .venv/bin/python -m mypy

typecheck-frontend:
	cd frontend && npm run check

build:
	cd frontend && npm run build

# ── AWS deployment ────────────────────────────────────────────────────────────

bootstrap:
	@if [ -z "$(ARTIFACTS_BUCKET)" ]; then \
		echo "Error: set ARTIFACTS_BUCKET=<name> before running bootstrap" >&2; exit 1; \
	fi
	aws s3api create-bucket \
		--bucket $(ARTIFACTS_BUCKET) \
		--region $(AWS_REGION) \
		$(if $(filter-out us-east-1,$(AWS_REGION)),--create-bucket-configuration LocationConstraint=$(AWS_REGION),)
	aws s3api put-bucket-versioning \
		--bucket $(ARTIFACTS_BUCKET) \
		--versioning-configuration Status=Enabled
	@echo "Artifacts bucket '$(ARTIFACTS_BUCKET)' ready."

deploy:
	@if [ -z "$(ARTIFACTS_BUCKET)" ]; then \
		echo "Error: set ARTIFACTS_BUCKET=<name> (run 'make bootstrap' first)" >&2; exit 1; \
	fi
	STACK_NAME=$(STACK_NAME) AWS_REGION=$(AWS_REGION) ARTIFACTS_BUCKET=$(ARTIFACTS_BUCKET) \
		./scripts/deploy.sh

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.mypy_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf frontend/node_modules frontend/.svelte-kit frontend/build
