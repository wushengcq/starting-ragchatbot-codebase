"""Shared fixtures and configuration for RAG system tests"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Import backend modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from ai_generator import AIGenerator
from rag_system import RAGSystem
from config import Config
from models import Course, Lesson, CourseChunk


# ============================================================================
# Sample Test Data
# ============================================================================

@pytest.fixture
def sample_lessons() -> List[Lesson]:
    """Create sample lesson data for testing"""
    return [
        Lesson(
            lesson_number=1,
            title="Introduction to MCP",
            lesson_link="https://example.com/mcp/lesson1"
        ),
        Lesson(
            lesson_number=2,
            title="Setting Up MCP Server",
            lesson_link="https://example.com/mcp/lesson2"
        ),
        Lesson(
            lesson_number=3,
            title="MCP Tools and Resources",
            lesson_link="https://example.com/mcp/lesson3"
        ),
    ]


@pytest.fixture
def sample_course(sample_lessons) -> Course:
    """Create a sample course for testing"""
    return Course(
        title="Model Context Protocol (MCP) Introduction",
        course_link="https://example.com/mcp-course",
        instructor="John Doe",
        lessons=sample_lessons
    )


@pytest.fixture
def sample_course_chunks(sample_course) -> List[CourseChunk]:
    """Create sample course chunks for testing"""
    chunks = [
        CourseChunk(
            content="MCP is a protocol for connecting AI assistants to external data sources. It enables context-aware interactions.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=0,
            lesson_link="https://example.com/mcp/lesson1"
        ),
        CourseChunk(
            content="To set up an MCP server, you need to define tools that the AI can use. Tools are functions that perform specific actions.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=1,
            lesson_link="https://example.com/mcp/lesson2"
        ),
        CourseChunk(
            content="MCP tools can be configured with parameters. The AI decides when to invoke each tool based on user queries.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=2,
            lesson_link="https://example.com/mcp/lesson2"
        ),
        CourseChunk(
            content="Resources in MCP include data connections and file access. Proper resource management is essential for security.",
            course_title=sample_course.title,
            lesson_number=3,
            chunk_index=3,
            lesson_link="https://example.com/mcp/lesson3"
        ),
    ]
    return chunks


@pytest.fixture
def sample_courses_multiple(sample_lessons) -> List[Course]:
    """Create multiple sample courses for testing"""
    lessons_rag = [
        Lesson(
            lesson_number=1,
            title="Introduction to RAG",
            lesson_link="https://example.com/rag/lesson1"
        ),
        Lesson(
            lesson_number=2,
            title="Vector Databases",
            lesson_link="https://example.com/rag/lesson2"
        ),
    ]

    return [
        Course(
            title="Model Context Protocol (MCP) Introduction",
            course_link="https://example.com/mcp-course",
            instructor="John Doe",
            lessons=sample_lessons
        ),
        Course(
            title="Introduction to RAG Systems",
            course_link="https://example.com/rag-course",
            instructor="Jane Smith",
            lessons=lessons_rag
        ),
    ]


# ============================================================================
# Mock Vector Store Fixtures
# ============================================================================

@pytest.fixture
def temp_chroma_path():
    """Create a temporary directory for ChromaDB test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_vector_store(temp_chroma_path):
    """Create a mock VectorStore for testing"""
    store = VectorStore(
        chroma_path=temp_chroma_path,
        embedding_model="all-MiniLM-L6-v2",
        max_results=5
    )
    return store


@pytest.fixture
def populated_vector_store(mock_vector_store, sample_course, sample_course_chunks):
    """Create a VectorStore populated with sample data"""
    # Add course metadata
    mock_vector_store.add_course_metadata(sample_course)

    # Add course content
    mock_vector_store.add_course_content(sample_course_chunks)

    return mock_vector_store


@pytest.fixture
def mock_search_results():
    """Create mock search results for testing"""
    return SearchResults(
        documents=[
            "MCP is a protocol for connecting AI assistants to external data sources.",
            "To set up an MCP server, you need to define tools that the AI can use.",
        ],
        metadata=[
            {
                "course_title": "Model Context Protocol (MCP) Introduction",
                "lesson_number": 1,
                "chunk_index": 0,
                "lesson_link": "https://example.com/mcp/lesson1"
            },
            {
                "course_title": "Model Context Protocol (MCP) Introduction",
                "lesson_number": 2,
                "chunk_index": 1,
                "lesson_link": "https://example.com/mcp/lesson2"
            },
        ],
        distances=[0.23, 0.34],
        error=None
    )


# ============================================================================
# Mock AI Generator Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Create a mock Config object for testing"""
    return Config(
        BIGMODEL_API_KEY="test-api-key-12345",
        BIGMODEL_MODEL="glm-5",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHROMA_PATH="./test_chroma_db"
    )


@pytest.fixture
def mock_ai_generator():
    """Create a mock AIGenerator for testing"""
    with patch('ai_generator.ZhipuAI') as mock_zhipuai:
        mock_client = MagicMock()
        mock_zhipuai.return_value = mock_client

        generator = AIGenerator(
            api_key="test-api-key",
            model="glm-5"
        )
        return generator


@pytest.fixture
def mock_glm_response():
    """Create a mock GLM API response"""
    mock_response = MagicMock()

    # Mock a response that doesn't use tools
    mock_response_no_tools = MagicMock()
    mock_response_no_tools.choices = [MagicMock()]
    mock_response_no_tools.choices[0].message.content = "This is a direct answer without tools."
    mock_response_no_tools.choices[0].message.tool_calls = None

    # Mock a response that uses tools
    mock_response_with_tools = MagicMock()
    mock_response_with_tools.choices = [MagicMock()]
    mock_response_with_tools.choices[0].message.content = None
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "search_course_content"
    mock_tool_call.function.arguments = '{"query": "MCP protocol", "course_name": "MCP"}'
    mock_response_with_tools.choices[0].message.tool_calls = [mock_tool_call]

    return {
        "no_tools": mock_response_no_tools,
        "with_tools": mock_response_with_tools
    }


# ============================================================================
# Tool Fixtures
# ============================================================================

@pytest.fixture
def course_search_tool(mock_vector_store):
    """Create a CourseSearchTool instance for testing"""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def course_outline_tool(mock_vector_store):
    """Create a CourseOutlineTool instance for testing"""
    return CourseOutlineTool(mock_vector_store)


@pytest.fixture
def tool_manager(course_search_tool, course_outline_tool):
    """Create a ToolManager with registered tools for testing"""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    manager.register_tool(course_outline_tool)
    return manager


# ============================================================================
# RAG System Fixtures
# ============================================================================

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
    with patch('rag_system.ZhipuAI'):
        rag = RAGSystem(config)
        return rag


@pytest.fixture
def populated_rag_system(mock_rag_system, sample_course, sample_course_chunks):
    """Create an RAGSystem populated with sample data"""
    # Add course to the system
    mock_rag_system.vector_store.add_course_metadata(sample_course)
    mock_rag_system.vector_store.add_course_content(sample_course_chunks)
    return mock_rag_system


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_search_results(documents, metadata, distances=None):
    """Helper to create SearchResults objects"""
    if distances is None:
        distances = [0.3] * len(documents)

    return SearchResults(
        documents=documents,
        metadata=metadata,
        distances=distances,
        error=None
    )


def create_empty_search_results(error_msg="No results found"):
    """Helper to create empty SearchResults"""
    return SearchResults.empty(error_msg)
