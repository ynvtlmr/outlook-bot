#!/usr/bin/env bash
# Pre-commit hook: runs ruff check and format on staged files
set -e

echo "Running pre-commit checks..."

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACMR -- '*.py')

if [ -z "$STAGED_PY_FILES" ]; then
    echo "No Python files staged. Skipping checks."
    exit 0
fi

echo "Checking ruff lint..."
uv run ruff check $STAGED_PY_FILES

echo "Checking ruff format..."
uv run ruff format --check $STAGED_PY_FILES

echo "Pre-commit checks passed."
