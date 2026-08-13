PYTHON_VERSION ?= 3.13
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: install install-backend install-frontend \
	dev dev-backend dev-frontend \
	test test-backend test-frontend \
	typecheck typecheck-backend typecheck-frontend \
	build clean

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

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.mypy_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf frontend/node_modules frontend/.svelte-kit frontend/build
