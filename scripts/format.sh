#!/bin/bash
# Format Python code with Black and isort

set -e

echo "Formatting Python code..."
echo "Running Black..."
cd backend && uv run black . --config ../pyproject.toml
cd ..

echo "Running isort..."
cd backend && uv run isort . --settings-path ../pyproject.toml
cd ..

echo "Code formatting complete!"
