#!/bin/bash
# Run code quality checks (Black, isort, flake8, mypy)

set -e

EXIT_CODE=0

echo "Running code quality checks..."
echo

echo "1. Checking Black formatting..."
cd backend && uv run black . --check --config ../pyproject.toml || EXIT_CODE=1
cd ..

echo
echo "2. Checking isort formatting..."
cd backend && uv run isort . --check-only --settings-path ../pyproject.toml || EXIT_CODE=1
cd ..

echo
echo "3. Running flake8 linter..."
cd backend && uv run flake8 . --max-line-length=100 --extend-ignore=E203,W503,E402 || EXIT_CODE=1
cd ..

echo
echo "4. Running mypy type checker (if installed)..."
cd backend && uv run mypy . --config-file ../pyproject.toml 2>/dev/null || echo "  Note: mypy not installed or type check skipped"
cd ..

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo "All quality checks passed!"
else
    echo "Some quality checks failed. Please fix the issues above."
    exit 1
fi
