"""Comprehensive tests for CourseSearchTool and CourseOutlineTool"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool functionality"""

    # ========================================================================
    # Basic Search Functionality
    # ========================================================================

    def test_basic_search(self, populated_vector_store):
        """Test searching with just a query string (no filters)"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="MCP protocol")

        # Should return formatted results with content
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Model Context Protocol" in result
        assert "MCP" in result

    def test_basic_search_returns_content(self, populated_vector_store):
        """Test that basic search returns actual content, not just metadata"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="tools and configuration")

        assert isinstance(result, str)
        # Should contain the actual text content from chunks
        assert "MCP tools" in result or "tools" in result.lower()

    def test_basic_search_case_insensitive(self, populated_vector_store):
        """Test that search is case insensitive"""
        tool = CourseSearchTool(populated_vector_store)

        result_lower = tool.execute(query="mcp protocol")
        result_upper = tool.execute(query="MCP PROTOCOL")
        result_mixed = tool.execute(query="Mcp Protocol")

        # All should return results
        assert len(result_lower) > 0
        assert len(result_upper) > 0
        assert len(result_mixed) > 0

    # ========================================================================
    # Filtered Search by Course
    # ========================================================================

    def test_search_with_course_filter_exact(self, populated_vector_store, sample_course):
        """Test with exact course name filter"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="protocol",
            course_name=sample_course.title
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert sample_course.title in result

    def test_search_with_course_filter_partial(self, populated_vector_store):
        """Test with partial course name matching"""
        tool = CourseSearchTool(populated_vector_store)

        # Use partial name "MCP" instead of full title
        result = tool.execute(
            query="protocol",
            course_name="MCP"
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_with_invalid_course(self, populated_vector_store):
        """Test with non-existent course name"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="something",
            course_name="NonExistentCourse123"
        )

        # Should return error message
        assert isinstance(result, str)
        assert "No course found" in result or "not found" in result.lower()

    # ========================================================================
    # Filtered Search by Lesson
    # ========================================================================

    def test_search_with_lesson_filter(self, populated_vector_store):
        """Test with lesson number filter"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="MCP",
            lesson_number=1
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Lesson 1" in result

    def test_search_with_nonexistent_lesson(self, populated_vector_store):
        """Test with lesson number that doesn't exist"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="MCP",
            lesson_number=999
        )

        # Should return no results message
        assert isinstance(result, str)
        assert "No relevant content found" in result

    # ========================================================================
    # Combined Filters
    # ========================================================================

    def test_search_with_combined_filters(self, populated_vector_store, sample_course):
        """Test with both course_name and lesson_number"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="protocol",
            course_name=sample_course.title,
            lesson_number=1
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert sample_course.title in result
        assert "Lesson 1" in result

    def test_search_with_invalid_course_valid_lesson(self, populated_vector_store):
        """Test with invalid course but valid lesson number"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="something",
            course_name="InvalidCourse",
            lesson_number=1
        )

        # Should fail on course validation first
        assert isinstance(result, str)
        assert "No course found" in result

    # ========================================================================
    # Output Format Tests
    # ========================================================================

    def test_output_format_with_headers(self, populated_vector_store):
        """Test that results include proper course and lesson headers"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="MCP protocol")

        # Check for proper formatting with [Course Title - Lesson N]
        assert "[" in result
        assert "]" in result
        assert "Lesson" in result

    def test_output_format_multiple_chunks(self, populated_vector_store):
        """Test that multiple chunks are formatted correctly"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="MCP")

        # Should have separators between chunks
        assert "\n\n" in result or len(result) > 100

    def test_output_format_without_lesson_number(self, mock_vector_store):
        """Test formatting when lesson_number is None"""
        tool = CourseSearchTool(mock_vector_store)

        # Add a chunk without lesson number
        from models import CourseChunk
        chunk = CourseChunk(
            content="Test content without lesson",
            course_title="Test Course",
            lesson_number=None,
            chunk_index=0
        )
        mock_vector_store.add_course_content([chunk])

        # Also need to add course metadata for resolution
        from models import Course, Lesson
        course = Course(
            title="Test Course",
            instructor="Test Instructor",
            lessons=[]
        )
        mock_vector_store.add_course_metadata(course)

        result = tool.execute(query="test content")

        # Should still work, just without "Lesson" in header
        assert isinstance(result, str)
        assert "Test Course" in result

    # ========================================================================
    # Source Tracking Tests
    # ========================================================================

    def test_source_tracking_populated(self, populated_vector_store):
        """Test that sources are tracked after search"""
        tool = CourseSearchTool(populated_vector_store)

        tool.execute(query="MCP protocol")

        # Check that last_sources was populated
        assert hasattr(tool, 'last_sources')
        assert len(tool.last_sources) > 0

        # Check source structure
        source = tool.last_sources[0]
        assert "text" in source
        assert isinstance(source["text"], str)

    def test_source_tracking_with_urls(self, populated_vector_store):
        """Test that sources include lesson URLs when available"""
        tool = CourseSearchTool(populated_vector_store)

        tool.execute(query="MCP protocol")

        # Check that sources have URLs
        for source in tool.last_sources:
            if "url" in source:
                assert source["url"] is not None
                assert isinstance(source["url"], str)
                assert source["url"].startswith("http")

    def test_source_deduplication(self, populated_vector_store):
        """Test that duplicate sources (same course+lesson) are deduplicated"""
        tool = CourseSearchTool(populated_vector_store)

        # Search that might return multiple chunks from same lesson
        tool.execute(query="MCP")

        # Extract unique (course, lesson) pairs from sources
        seen_pairs = set()
        for source in tool.last_sources:
            # Extract lesson number from text like "Course - Lesson N"
            text = source["text"]
            # Should not have duplicates of the same course+lesson
            key = text
            assert key not in seen_pairs, f"Duplicate source found: {text}"
            seen_pairs.add(key)

    def test_sources_reset_on_new_search(self, populated_vector_store):
        """Test that sources are updated on new search"""
        tool = CourseSearchTool(populated_vector_store)

        # First search
        tool.execute(query="protocol")
        first_sources = tool.last_sources.copy()

        # Second search with different query
        tool.execute(query="tools")
        second_sources = tool.last_sources

        # Sources should still exist (not empty)
        assert len(second_sources) > 0

    # ========================================================================
    # Edge Cases and Error Handling
    # ========================================================================

    def test_search_empty_query(self, populated_vector_store):
        """Test with empty query string"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="")

        # Should handle gracefully - may return results or error
        assert isinstance(result, str)

    def test_search_no_matches(self, populated_vector_store):
        """Test with query that matches nothing"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="xyzabc123nonexistent")

        # Should return "no relevant content" message
        assert isinstance(result, str)
        assert "No relevant content found" in result or len(result) == 0

    def test_search_with_special_characters(self, populated_vector_store):
        """Test with special characters in query"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="MCP & AI, (protocol)")

        # Should handle special characters without crashing
        assert isinstance(result, str)

    def test_search_with_unicode(self, populated_vector_store):
        """Test with unicode characters in query"""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="MCP protocol — test")

        # Should handle unicode without issues
        assert isinstance(result, str)

    def test_vector_store_error_handling(self, mock_vector_store):
        """Test behavior when vector store raises an error"""
        tool = CourseSearchTool(mock_vector_store)

        # Mock the search method to raise an exception
        with patch.object(mock_vector_store, 'search', side_effect=Exception("DB Error")):
            result = tool.execute(query="test")

            # Should return error message
            assert isinstance(result, str)
            assert "Search error" in result or "error" in result.lower()

    # ========================================================================
    # Tool Definition Tests
    # ========================================================================

    def test_tool_definition_structure(self, mock_vector_store):
        """Test that tool definition is properly structured"""
        tool = CourseSearchTool(mock_vector_store)

        definition = tool.get_tool_definition()

        # Check required fields
        assert "name" in definition
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition

        # Check input schema
        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "course_name" in schema["properties"]
        assert "lesson_number" in schema["properties"]

        # Check required parameters
        assert "query" in schema["required"]
        assert "course_name" not in schema["required"]  # Optional
        assert "lesson_number" not in schema["required"]  # Optional


class TestCourseOutlineTool:
    """Test suite for CourseOutlineTool functionality"""

    # ========================================================================
    # Basic Outline Functionality
    # ========================================================================

    def test_get_outline_with_valid_course(self, populated_vector_store, sample_course):
        """Test retrieving outline for an existing course"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title=sample_course.title)

        assert isinstance(result, str)
        assert "Course:" in result
        assert sample_course.title in result
        assert "Instructor:" in result
        assert "Lessons:" in result

    def test_get_outline_with_partial_title(self, populated_vector_store):
        """Test retrieving outline with partial course title"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title="MCP")

        assert isinstance(result, str)
        assert "Course:" in result
        assert "Lessons:" in result

    def test_get_outline_nonexistent_course(self, populated_vector_store):
        """Test retrieving outline for non-existent course"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title="NonExistentCourse")

        assert isinstance(result, str)
        assert "No course found" in result

    def test_outline_includes_all_lessons(self, populated_vector_store, sample_course):
        """Test that outline includes all lessons with numbers"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title=sample_course.title)

        # Should include all lessons (sample has 3)
        for lesson in sample_course.lessons:
            assert f"Lesson {lesson.lesson_number}" in result
            assert lesson.title in result

    def test_outline_includes_course_link(self, populated_vector_store, sample_course):
        """Test that outline includes course link when available"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title=sample_course.title)

        assert "Course Link:" in result
        assert sample_course.course_link in result

    def test_outline_includes_lesson_count(self, populated_vector_store, sample_course):
        """Test that outline shows total lesson count"""
        tool = CourseOutlineTool(populated_vector_store)

        result = tool.execute(course_title=sample_course.title)

        assert "Total Lessons:" in result
        assert str(len(sample_course.lessons)) in result

    # ========================================================================
    # Tool Definition Tests
    # ========================================================================

    def test_outline_tool_definition(self, mock_vector_store):
        """Test that CourseOutlineTool definition is properly structured"""
        tool = CourseOutlineTool(mock_vector_store)

        definition = tool.get_tool_definition()

        # Check required fields
        assert "name" in definition
        assert definition["name"] == "get_course_outline"
        assert "description" in definition
        assert "input_schema" in definition

        # Check input schema
        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "course_title" in schema["properties"]
        assert "course_title" in schema["required"]


class TestToolManager:
    """Test suite for ToolManager functionality"""

    # ========================================================================
    # Tool Registration
    # ========================================================================

    def test_register_tool(self, tool_manager, course_search_tool):
        """Test registering a tool"""
        assert "search_course_content" in tool_manager.tools
        assert tool_manager.tools["search_course_content"] == course_search_tool

    def test_register_multiple_tools(self, tool_manager):
        """Test registering multiple tools"""
        definitions = tool_manager.get_tool_definitions()

        assert len(definitions) == 2
        tool_names = [tool["name"] for tool in definitions]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_register_tool_without_name(self):
        """Test that registering tool without name raises error"""
        manager = ToolManager()

        # Create a mock tool without name
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {"description": "test"}

        with pytest.raises(ValueError, match="Tool must have a 'name'"):
            manager.register_tool(mock_tool)

    # ========================================================================
    # Tool Execution
    # ========================================================================

    def test_execute_tool_success(self, tool_manager, populated_vector_store):
        """Test successful tool execution"""
        result = tool_manager.execute_tool(
            "search_course_content",
            query="MCP protocol"
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_tool_not_found(self, tool_manager):
        """Test executing non-existent tool"""
        result = tool_manager.execute_tool("nonexistent_tool", param="value")

        assert "not found" in result.lower()

    def test_execute_tool_with_parameters(self, tool_manager, populated_vector_store):
        """Test tool execution with multiple parameters"""
        result = tool_manager.execute_tool(
            "search_course_content",
            query="protocol",
            course_name="MCP",
            lesson_number=1
        )

        assert isinstance(result, str)

    # ========================================================================
    # Source Tracking
    # ========================================================================

    def test_get_last_sources(self, tool_manager, populated_vector_store):
        """Test retrieving sources from last search"""
        # Execute a search first
        tool_manager.execute_tool("search_course_content", query="MCP")

        sources = tool_manager.get_last_sources()

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "text" in sources[0]

    def test_get_last_sources_no_search(self, tool_manager):
        """Test getting sources when no search has been performed"""
        sources = tool_manager.get_last_sources()

        assert isinstance(sources, list)
        assert len(sources) == 0

    def test_reset_sources(self, tool_manager, populated_vector_store):
        """Test resetting sources"""
        # Execute a search to populate sources
        tool_manager.execute_tool("search_course_content", query="MCP")
        assert len(tool_manager.get_last_sources()) > 0

        # Reset sources
        tool_manager.reset_sources()
        assert len(tool_manager.get_last_sources()) == 0

    def test_get_tool_definitions_format(self, tool_manager):
        """Test that get_tool_definitions returns proper format"""
        definitions = tool_manager.get_tool_definitions()

        assert isinstance(definitions, list)
        for definition in definitions:
            assert isinstance(definition, dict)
            assert "name" in definition
            assert "description" in definition
            assert "input_schema" in definition
