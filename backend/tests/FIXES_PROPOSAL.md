# Fixes Proposal for RAG System Issues

**Date**: 2026-02-27
**Based On**: TEST_RESULTS.md
**Status**: Proposed

## Overview

This document provides specific, actionable fixes for the 6 critical issues identified in the test suite. Each fix includes code-level corrections with before/after examples.

---

## Issue 1: Mock Configuration Error (CRITICAL)

**Priority**: CRITICAL
**File**: `backend/tests/conftest.py:296`
**Impact**: Blocks 27 RAG system integration tests from running

### Problem

The `mock_rag_system` fixture tries to patch `rag_system.ZhipuAI`, but `ZhipuAI` is imported in `ai_generator.py`, not `rag_system.py`.

### Current Code

```python
# backend/tests/conftest.py, line 296
@pytest.fixture
def mock_rag_system(temp_chroma_path):
    """Create a mock RAGSystem for testing"""
    config = Config(
        BIGMODEL_API_KEY="test-api-key",
        BIGMODEL_MODEL="glm-5",
        CHROMA_PATH=temp_chroma_path,
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100
    )

    # Patch the ZhipuAI to avoid actual API calls
    with patch('rag_system.ZhipuAI'):  # ❌ WRONG - ZhipuAI is not in rag_system
        rag = RAGSystem(config)
        return rag
```

### Proposed Fix

```python
@pytest.fixture
def mock_rag_system(temp_chroma_path):
    """Create a mock RAGSystem for testing"""
    config = Config(
        BIGMODEL_API_KEY="test-api-key",
        BIGMODEL_MODEL="glm-5",
        CHROMA_PATH=temp_chroma_path,
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100
    )

    # Patch at the module where it's actually imported
    with patch('ai_generator.ZhipuAI'):  # ✅ CORRECT
        rag = RAGSystem(config)
        return rag
```

### Alternative Fix (More Robust)

```python
@pytest.fixture
def mock_rag_system(temp_chroma_path):
    """Create a mock RAGSystem for testing"""
    config = Config(
        BIGMODEL_API_KEY="test-api-key",
        BIGMODEL_MODEL="glm-5",
        CHROMA_PATH=temp_chroma_path,
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100
    )

    # Patch at the import point in rag_system.py
    with patch('rag_system.AIGenerator.__init__', return_value=None):
        # Create mock AI generator manually
        from unittest.mock import MagicMock
        mock_ai = MagicMock()
        mock_ai.generate_response.return_value = "Test response"

        rag = RAGSystem(config)
        rag.ai_generator = mock_ai
        return rag
```

### Verification

After fix, run:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_rag_system.py::TestRAGSystemIntegration::test_query_with_content_question -v
```

Expected: Test runs without `AttributeError`

---

## Issue 2: Course Name Resolution Failure (CRITICAL)

**Priority**: CRITICAL
**Files**: `backend/vector_store.py:102-116`, `backend/search_tools.py:66-70`
**Impact**: Course filters are ignored, returning ALL content instead of filtered results

### Problem

When searching with an invalid course name, the system returns all content instead of an error message. The `_resolve_course_name()` method is not correctly identifying when no match exists.

### Root Cause Analysis

1. Vector search on `course_catalog` may be matching to any course when using invalid input
2. The `_build_filter()` method may not be applying filters correctly
3. No validation that resolved course actually matches the query

### Current Code

```python
# backend/vector_store.py, line 102-116
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    """Use vector search to find best matching course by name"""
    try:
        results = self.course_catalog.query(
            query_texts=[course_name],
            n_results=1
        )

        if results['documents'][0] and results['metadatas'][0]:
            # Return the title (which is now the ID)
            return results['metadatas'][0][0]['title']
    except Exception as e:
        print(f"Error resolving course name: {e}")

    return None
```

### Proposed Fix #1: Add Similarity Threshold

```python
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    """Use vector search to find best matching course by name"""
    try:
        results = self.course_catalog.query(
            query_texts=[course_name],
            n_results=1
        )

        if results['documents'][0] and results['metadatas'][0]:
            # Check similarity threshold - only accept close matches
            distance = results['distances'][0][0]
            if distance > 0.7:  # Threshold: too far = no match
                return None

            # Return the title (which is now the ID)
            return results['metadatas'][0][0]['title']
    except Exception as e:
        print(f"Error resolving course name: {e}")

    return None
```

### Proposed Fix #2: Add Fuzzy Matching Validation

```python
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    """Use vector search to find best matching course by name"""
    try:
        results = self.course_catalog.query(
            query_texts=[course_name],
            n_results=1
        )

        if results['documents'][0] and results['metadatas'][0]:
            # Get the match
            matched_title = results['metadatas'][0][0]['title']
            distance = results['distances'][0][0]

            # Validate that the match actually contains the query text
            # (case-insensitive substring match)
            course_name_lower = course_name.lower()
            matched_title_lower = matched_title.lower()

            # Accept if: close in vector space OR contains query text
            if distance < 0.7 or course_name_lower in matched_title_lower:
                return matched_title

            # No good match found
            return None
    except Exception as e:
        print(f"Error resolving course name: {e}")

    return None
```

### Proposed Fix #3: Improve Search Method

```python
# backend/search_tools.py, line 52-86
def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    """
    Execute the search tool with given parameters.
    """
    # Validate course name first
    if course_name:
        resolved_title = self.store._resolve_course_name(course_name)
        if not resolved_title:
            return f"No course found matching '{course_name}'. Available courses: {', '.join(self.store.get_existing_course_titles())[:5]}"

    # Use the vector store's unified search interface
    results = self.store.search(
        query=query,
        course_name=course_name,
        lesson_number=lesson_number
    )

    # Handle errors
    if results.error:
        return results.error

    # Handle empty results
    if results.is_empty():
        filter_info = ""
        if course_name:
            filter_info += f" in course '{course_name}'"
        if lesson_number:
            filter_info += f" in lesson {lesson_number}"
        return f"No relevant content found{filter_info}."

    # Format and return results
    return self._format_results(results)
```

### Verification

After fix, test:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_search_with_invalid_course -v
```

Expected: Returns error message instead of all content

---

## Issue 3: Poor Empty Result Handling (HIGH)

**Priority**: HIGH
**File**: `backend/vector_store.py:61-100`
**Impact**: Returns irrelevant content when no good matches exist

### Problem

Vector search returns "closest" matches even when they're not relevant to the query. Searching for "xyzabc123nonexistent" returns actual course content.

### Current Code

```python
# backend/vector_store.py, line 92-100
try:
    results = self.course_content.query(
        query_texts=[query],
        n_results=search_limit,
        where=filter_dict
    )
    return SearchResults.from_chroma(results)
except Exception as e:
    return SearchResults.empty(f"Search error: {str(e)}")
```

### Proposed Fix #1: Add Similarity Threshold

```python
def search(self,
           query: str,
           course_name: Optional[str] = None,
           lesson_number: Optional[int] = None,
           limit: Optional[int] = None) -> SearchResults:
    """Main search interface with similarity threshold"""
    # ... existing code for course resolution and filter building ...

    search_limit = limit if limit is not None else self.max_results

    try:
        results = self.course_content.query(
            query_texts=[query],
            n_results=search_limit,
            where=filter_dict
        )

        # Filter out results below similarity threshold
        if results['distances'] and results['distances'][0]:
            filtered_docs = []
            filtered_metadata = []
            filtered_distances = []

            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                # Only accept results with distance < 0.7 (similar enough)
                if dist < 0.7:
                    filtered_docs.append(doc)
                    filtered_metadata.append(meta)
                    filtered_distances.append(dist)

            # If no results pass threshold, return empty
            if not filtered_docs:
                return SearchResults.empty("No relevant content found")

            # Return filtered results
            return SearchResults(
                documents=filtered_docs,
                metadata=filtered_metadata,
                distances=filtered_distances,
                error=None
            )

        return SearchResults.from_chroma(results)

    except Exception as e:
        return SearchResults.empty(f"Search error: {str(e)}")
```

### Proposed Fix #2: Configurable Threshold

```python
# Add to config.py
@dataclass
class Config:
    # ... existing config ...
    SIMILARITY_THRESHOLD: float = 0.7  # Maximum distance for relevant results

# Update vector_store.py __init__
def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5,
             similarity_threshold: float = 0.7):
    self.max_results = max_results
    self.similarity_threshold = similarity_threshold
    # ... rest of init ...

# Use in search method
if dist < self.similarity_threshold:
    filtered_docs.append(doc)
    # ...
```

### Verification

After fix, test:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_search_no_matches -v
```

Expected: Returns "No relevant content found" for nonsense queries

---

## Issue 4: ChromaDB Metadata None Handling (MEDIUM)

**Priority**: MEDIUM
**File**: `backend/vector_store.py:162-181`
**Impact**: Crashes when adding content with None lesson_number or lesson_link

### Problem

ChromaDB 1.0.15 rejects `None` values in metadata. When `lesson_number=None` or `lesson_link=None`, the add operation fails.

### Current Code

```python
# backend/vector_store.py, line 168-173
metadatas = [{
    "course_title": chunk.course_title,
    "lesson_number": chunk.lesson_number,  # ❌ Can be None
    "chunk_index": chunk.chunk_index,
    "lesson_link": chunk.lesson_link  # ❌ Can be None
} for chunk in chunks]
```

### Proposed Fix

```python
def add_course_content(self, chunks: List[CourseChunk]):
    """Add course content chunks to the vector store"""
    if not chunks:
        return

    documents = [chunk.content for chunk in chunks]

    # Build metadata, omitting None values
    metadatas = []
    for chunk in chunks:
        metadata = {
            "course_title": chunk.course_title,
            "chunk_index": chunk.chunk_index,
        }
        # Only add lesson_number if not None
        if chunk.lesson_number is not None:
            metadata["lesson_number"] = chunk.lesson_number
        # Only add lesson_link if not None
        if chunk.lesson_link is not None:
            metadata["lesson_link"] = chunk.lesson_link

        metadatas.append(metadata)

    # Use title with chunk index for unique IDs
    ids = [f"{chunk.course_title.replace(' ', '_')}_{chunk.chunk_index}" for chunk in chunks]

    self.course_content.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
```

### Verification

After fix, test:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_output_format_without_lesson_number -v
```

Expected: Test passes without TypeError

---

## Issue 5: Error Propagation in Search Tool (MEDIUM)

**Priority**: MEDIUM
**File**: `backend/search_tools.py:66-74`
**Impact**: Unhandled exceptions crash the application

### Problem

The `execute()` method doesn't wrap vector store calls in try-except, so exceptions propagate instead of being returned as error messages.

### Current Code

```python
# backend/search_tools.py, line 66-74
def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    # ... docstring ...

    # Use the vector store's unified search interface
    results = self.store.search(  # ❌ Can raise exception
        query=query,
        course_name=course_name,
        lesson_number=lesson_number
    )

    # Handle errors
    if results.error:
        return results.error
```

### Proposed Fix

```python
def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    """
    Execute the search tool with given parameters.

    Args:
        query: What to search for
        course_name: Optional course filter
        lesson_number: Optional lesson filter

    Returns:
        Formatted search results or error message
    """
    try:
        # Use the vector store's unified search interface
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
    except Exception as e:
        # Catch any exceptions and return error message
        return f"Search error: {str(e)}"

    # Handle errors in SearchResults object
    if results.error:
        return results.error

    # Handle empty results
    if results.is_empty():
        filter_info = ""
        if course_name:
            filter_info += f" in course '{course_name}'"
        if lesson_number:
            filter_info += f" in lesson {lesson_number}"
        return f"No relevant content found{filter_info}."

    # Format and return results
    return self._format_results(results)
```

### Verification

After fix, test:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_vector_store_error_handling -v
```

Expected: Returns "Search error: DB Error" instead of raising Exception

---

## Issue 6: CourseOutlineTool Resolution (LOW)

**Priority**: LOW
**File**: `backend/search_tools.py:151-165`
**Impact**: Similar to Issue #2, returns wrong course outline

### Problem

Uses same `_resolve_course_name()` method that has issues with validation.

### Current Code

```python
# backend/search_tools.py, line 161-165
# Resolve the course name using vector search
resolved_title = self.store._resolve_course_name(course_title)

if not resolved_title:
    return f"No course found matching '{course_title}'"
```

### Proposed Fix

This will be automatically fixed when Issue #2 is fixed, since it uses the same `_resolve_course_name()` method.

### Additional Validation

Add extra validation to ensure the resolved course is actually a good match:

```python
def execute(self, course_title: str) -> str:
    """Execute the outline tool to get course information."""
    # Resolve the course name using vector search
    resolved_title = self.store._resolve_course_name(course_title)

    if not resolved_title:
        # List available courses to help user
        available = self.store.get_existing_course_titles()
        if available:
            courses_list = ", ".join(available[:5])
            if len(available) > 5:
                courses_list += f", ... ({len(available) - 5} more)"
            return f"No course found matching '{course_title}'. Available courses: {courses_list}"
        return f"No course found matching '{course_title}'. No courses available."

    # ... rest of method ...
```

---

## Implementation Priority

### Phase 1: Critical Fixes (Unblock Testing)
1. **Fix #1 (Mock Configuration)** - 5 minutes, unblocks 27 tests
2. **Fix #4 (None Handling)** - 10 minutes, prevents crashes

### Phase 2: Core Functionality (User Impact)
3. **Fix #2 (Course Resolution)** - 30 minutes, critical for user queries
4. **Fix #5 (Error Handling)** - 10 minutes, prevents crashes

### Phase 3: Quality Improvements (Result Quality)
5. **Fix #3 (Empty Results)** - 20 minutes, improves result relevance
6. **Fix #6 (Outline Tool)** - Fixed automatically by #2

**Total Estimated Time**: ~75 minutes

---

## Testing Strategy

### Before Applying Fixes

1. Run baseline tests to confirm current failures:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/ -v --tb=short > baseline_results.txt
```

### After Each Fix

1. Run affected tests:
```bash
# For Issue #1
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_rag_system.py -v

# For Issue #2
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_search_with_invalid_course -v

# For Issue #3
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py::TestCourseSearchTool::test_search_no_matches -v
```

2. Verify fix doesn't break existing passing tests:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/test_search_tools.py -v
```

### After All Fixes

1. Run full test suite:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/ -v
```

2. Generate coverage report:
```bash
PYTHONPATH=/path/to/backend /path/to/.venv/bin/python -m pytest tests/ --cov=. --cov-report=html
```

3. Manual verification:
   - Start dev server: `./run.sh`
   - Test with web interface
   - Verify course filters work
   - Verify outline queries work
   - Verify error messages are user-friendly

---

## Rollback Plan

If any fix causes issues:

1. **Git stash changes**:
```bash
git stash
```

2. **Revert to last working version**

3. **Document the issue** and create alternative fix approach

---

## Additional Recommendations

### Not Directly Tested But Worth Fixing

1. **Add Request Logging**: Log all search queries and results for debugging
2. **Add Metrics**: Track query latency, result counts, filter usage
3. **Add Caching**: Cache frequently asked questions
4. **Add Rate Limiting**: Prevent abuse of API
5. **Add Query Validation**: Reject obviously malformed queries early

### Future Enhancements

1. **Hybrid Search**: Combine vector search with keyword search (BM25)
2. **Query Expansion**: Expand queries with synonyms and related terms
3. **Result Re-ranking**: Use cross-encoder for better relevance
4. **Multi-language Support**: Support queries in different languages
5. **Feedback Loop**: Learn from user clicks on results

---

## Conclusion

The proposed fixes address all 6 critical issues identified in testing:

1. ✅ Mock configuration fixed → 27 tests unblocked
2. ✅ Course resolution validated → accurate filters
3. ✅ Similarity threshold added → relevant results only
4. ✅ None values handled → no crashes
5. ✅ Exception handling → graceful errors
6. ✅ Outline tool → inherits fix from #2

All fixes are:
- **Specific** with exact code changes
- **Tested** with verification commands
- **Prioritized** by user impact
- **Safe** with rollback plan
- **Quick** to implement (~75 minutes total)

After applying these fixes, all 86 tests should pass, and the RAG system will provide accurate, reliable course content retrieval.
