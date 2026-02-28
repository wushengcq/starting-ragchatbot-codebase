#!/bin/bash
# Run all quality checks including tests

set -e

echo "Running complete quality check suite..."
echo

./scripts/lint.sh

echo
echo "5. Running tests..."
cd backend && uv run pytest -v
cd ..

echo
echo "All checks passed successfully!"
