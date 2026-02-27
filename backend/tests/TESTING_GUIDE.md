# Quick Testing Guide

## Setup (One-Time)

```bash
# Install pytest in the project virtual environment
uv pip install --python .venv/bin/python pytest pytest-mock pytest-cov

# Verify installation
.venv/bin/python -m pytest --version
```

## Running Tests

### Run All Tests
```bash
# From project root directory
PYTHONPATH=/Users/ws/Temp/claude_tutorial/starting-ragchatbot-codebase/backend \
.venv/bin/python -m pytest backend/tests/ -v
```

### Run Specific Test File
```bash
# Search tools tests only
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/test_search_tools.py -v

# AI generator tests only
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/test_ai_generator.py -v

# RAG system tests only
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/test_rag_system.py -v
```

### Run Specific Test
```bash
# Single test
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest \
  backend/tests/test_search_tools.py::TestCourseSearchTool::test_basic_search -v

# All tests in a class
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest \
  backend/tests/test_search_tools.py::TestCourseSearchTool -v
```

### Run with Coverage Report
```bash
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ \
  --cov=. --cov-report=html --cov-report=term
```

### Run Failed Tests Only
```bash
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ -v \
  --lf  # last-failed
```

## Test Output Locations

- **Console**: Verbose test results printed to terminal
- **Full Output**: `backend/tests/test_run_full_output.txt`
- **Coverage Report**: `htmlcov/index.html` (when using --cov-report=html)

## Current Test Status

As of 2026-02-27:

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Pass | 52 | 60.5% |
| ❌ Fail | 7 | 8.1% |
| ⚠️  Error | 27 | 31.4% |
| **Total** | **86** | **100%** |

## Quick Diagnostics

### See What Tests Are Failing
```bash
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ -v \
  --tb=no | grep -E "(FAILED|ERROR)"
```

### Count Tests by Status
```bash
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ -v \
  --tb=no | tail -1
```

### Run Tests in Parallel (Faster)
```bash
# Install pytest-xdist first
uv pip install --python .venv/bin/python pytest-xdist

# Run with 4 workers
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ -v -n 4
```

## Troubleshooting

### Import Error: No module named 'chromadb'
```bash
# Make sure dependencies are installed
uv sync

# Or install directly
uv pip install --python .venv/bin/python chromadb
```

### ModuleNotFoundError: No module named 'backend'
```bash
# Make sure PYTHONPATH is set correctly
export PYTHONPATH=/path/to/project/backend
.venv/bin/python -m pytest backend/tests/ -v
```

### Tests Can't Find Fixtures
```bash
# Make sure you're running from the correct directory
# Tests should be run from: project root directory
# Not from: backend/tests/ directory

pwd  # Should be: /path/to/starting-ragchatbot-codebase
```

## Understanding Test Results

### Pass ✅
```
PASSED backend/tests/test_search_tools.py::TestCourseSearchTool::test_basic_search
```
Test executed successfully and all assertions passed.

### Fail ❌
```
FAILED backend/tests/test_search_tools.py::TestCourseSearchTool::test_search_with_invalid_course
AssertionError: assert 'No course found' in result
```
Test ran but an assertion failed. Check the error message to see what went wrong.

### Error ⚠️
```
ERROR backend/tests/test_rag_system.py - AttributeError: module 'rag_system' has no attribute 'ZhipuAI'
```
Test couldn't run due to setup/configuration error. Usually a fixture or import issue.

## Test Files Overview

### `test_search_tools.py` (50 tests)
Tests for CourseSearchTool, CourseOutlineTool, and ToolManager.
- Basic search functionality
- Filtered searches (by course, lesson)
- Output formatting
- Source tracking
- Error handling

### `test_ai_generator.py` (7 tests)
Tests for AIGenerator tool calling.
- Tool format conversion (Anthropic → GLM)
- Tool invocation decisions
- Parameter passing
- Response handling
- Error scenarios

### `test_rag_system.py` (29 tests)
Integration tests for the complete RAG system.
- End-to-end query flow
- Vector store integration
- Tool manager coordination
- Source tracking
- Conversation history
- Error scenarios

## Documentation

- **TEST_RESULTS.md** - Detailed test analysis and issue identification
- **FIXES_PROPOSAL.md** - Specific code fixes for all identified issues
- **IMPLEMENTATION_SUMMARY.md** - Summary of what was accomplished

## Getting Help

1. Check TEST_RESULTS.md for detailed analysis of failures
2. Check FIXES_PROPOSAL.md for specific code fixes
3. Run tests with `-v` flag for verbose output
4. Run tests with `-s` flag to see print statements
5. Check test docstrings: `pytest --collect-only backend/tests/`

## Best Practices

1. **Run tests before committing changes**
2. **Add new tests for new features**
3. **Keep tests fast** (mock external dependencies)
4. **Use descriptive test names** (test_what_you_expect_to_happen)
5. **One assertion per test** when possible
6. **Use fixtures** to reduce duplication
7. **Test edge cases** not just happy paths
8. **Keep test data simple** and minimal

## Example Workflow

```bash
# 1. Make your code changes
vim backend/search_tools.py

# 2. Run the affected tests
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest \
  backend/tests/test_search_tools.py::TestCourseSearchTool -v

# 3. If tests fail, investigate
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest \
  backend/tests/test_search_tools.py::TestCourseSearchTool::test_search_with_invalid_course \
  -v -s

# 4. Fix the issue and re-test
# ... edit code ...

# 5. Run all tests to ensure nothing broke
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ -v

# 6. Generate coverage report (optional)
PYTHONPATH=/path/to/backend .venv/bin/python -m pytest backend/tests/ \
  --cov=. --cov-report=html

# 7. Commit if all tests pass
git add backend/search_tools.py
git commit -m "Fix course name resolution issue"
```

## Continuous Integration

To add this to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: |
          PYTHONPATH=${{github.workspace}}/backend \
          .venv/bin/python -m pytest backend/tests/ -v
```

---

For detailed information about test results and fixes, see:
- **TEST_RESULTS.md** - What's broken and why
- **FIXES_PROPOSAL.md** - How to fix it
- **IMPLEMENTATION_SUMMARY.md** - What we accomplished
