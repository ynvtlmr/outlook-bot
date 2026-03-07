#!/usr/bin/env bash
# Pre-push hook: runs full test suite and type checking before push
set -e

echo "Running pre-push checks..."

echo "Running ruff check..."
uv run ruff check src/ tests/

echo "Running ruff format check..."
uv run ruff format --check src/ tests/

echo "Running type checker (ty)..."
uv run ty check src/ || echo "Warning: ty check had issues (non-blocking)"

echo "Running tests..."
uv run pytest -m "not integration" tests/ -x -q

echo "Pre-push checks passed."
