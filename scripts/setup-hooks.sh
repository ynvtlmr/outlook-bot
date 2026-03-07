#!/usr/bin/env bash
# Install git hooks by symlinking to the scripts directory.
# Run once after cloning: ./scripts/setup-hooks.sh

set -e

HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"
SCRIPTS_DIR="$(git rev-parse --show-toplevel)/scripts"

echo "Installing git hooks..."

ln -sf "$SCRIPTS_DIR/pre-commit.sh" "$HOOKS_DIR/pre-commit"
ln -sf "$SCRIPTS_DIR/pre-push.sh" "$HOOKS_DIR/pre-push"

echo "Git hooks installed successfully."
echo "  pre-commit -> ruff lint + format check on staged files"
echo "  pre-push   -> full lint + type check + test suite"
