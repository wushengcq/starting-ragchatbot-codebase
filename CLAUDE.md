# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system for querying course materials. Users can ask questions about educational content and receive intelligent, context-aware responses powered by semantic search and GLM AI.

**Tech Stack**: Python 3.13+ (FastAPI backend), vanilla JavaScript (frontend), ChromaDB (vector store), BigModel GLM-5 (AI generation)

## Development Commands

```bash
# Install dependencies
uv sync

# Start development server (recommended)
./run.sh

# Start manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Prerequisites**:
- Python 3.13+
- uv package manager
- `BIGMODEL_API_KEY` in `.env` file (BigModel GLM API key)

**Server endpoints**:
- Web interface: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Architecture

The system follows a modular pipeline architecture. Each component has a single responsibility and is coordinated by the central RAG system.

### Core Pipeline Flow

1. **Document Ingestion**: Course documents in `/docs/` are parsed, chunked, and vectorized on startup
2. **Vector Storage**: Two ChromaDB collections store course metadata and content chunks separately
3. **Query Processing**: User queries are processed with conversation context
4. **Tool-Based Search**: Claude decides when to invoke the search tool based on the query
5. **AI Generation**: Claude generates responses using retrieved context
6. **Response Delivery**: Answers are returned with source attribution

### Key Backend Components

**`rag_system.py`** - Central orchestrator. Initializes all components and coordinates the flow. Key methods:
- `add_course_folder()` - Loads documents from `/docs/` on startup
- `query()` - Processes user queries with conversation context

**`search_tools.py`** - Implements tool-based AI integration with two tools:
- `CourseSearchTool`: Provides `search_course_content` for searching course materials with optional filters (course_name, lesson_name)
- `CourseOutlineTool`: Provides `get_course_outline` for retrieving course structure and lesson lists

This gives the AI control over when to search and when to get course structure, rather than forcing retrieval on every query.

**`vector_store.py`** - ChromaDB wrapper managing two collections:
- `course_catalog` - For semantic course discovery
- `course_content` - For detailed lesson content retrieval

**`document_processor.py`** - Parses structured text files. Extracts course metadata (title, instructor, lessons) and creates overlapping text chunks (default: 800 chars with 100 char overlap).

**`ai_generator.py`** - BigModel GLM integration. Handles tool calling and response generation with conversation history using the glm-5 model.

**`session_manager.py`** - Manages conversation state and history for multi-turn context.

**`app.py`** - FastAPI application with three main endpoints:
- `POST /api/query` - Process user queries
- `GET /api/courses` - Get course statistics
- `POST /api/clear-session` - Clear conversation session history

Auto-loads documents from `/docs/` on startup via `startup_event()`.

**`config.py`** - Centralized configuration using dataclasses. Key settings:
- `CHUNK_SIZE`: 800 (text chunk size)
- `CHUNK_OVERLAP`: 100 (characters between chunks)
- `MAX_RESULTS`: 5 (search results to return)
- `MAX_HISTORY`: 2 (conversation turns to remember)
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2"
- `BIGMODEL_MODEL`: "glm-5"

### Frontend

Vanilla JavaScript in `/frontend/`:
- `index.html` - Single-page application structure
- `style.css` - Responsive styling with sidebar layout
- `script.js` - API client for querying backend

**Features**:
- New Chat button for starting fresh conversation sessions
- Clickable source citations with direct links to lesson videos
- Course statistics displayed in sidebar
- Real-time query/response streaming

Static files are served directly by FastAPI with no-cache headers for development.

## Document Format

Course documents in `/docs/` follow a structured text format:

```
Title: [Course Title]
Instructor: [Instructor Name]
Course Link: [Course URL]

## [Lesson 1 Name]
Lesson Link: [Lesson URL]

[Lesson content...]

## [Lesson 2 Name]
Lesson Link: [Lesson URL]

[Lesson content...]
```

**Fields**:
- `Title` - Course name (required)
- `Instructor` - Instructor name (required)
- `Course Link` - URL to the course page (optional)
- `## [Lesson Name]` - Lesson headers with links below (required)

Documents are automatically loaded on startup. The system tracks existing courses by title and skips duplicates.

## Tool-Based AI Integration

The system uses GLM's function calling capabilities with two tools:

**1. CourseSearchTool (`search_course_content`)**:
- Searches course content using semantic similarity
- Optional filters: `course_name`, `lesson_name`
- Returns relevant chunks with metadata (course, lesson, position)

**2. CourseOutlineTool (`get_course_outline`)**:
- Retrieves course structure and lesson lists
- No parameters required
- Returns organized course/lesson hierarchy

When processing a query:

1. The AI receives the user query + available tool definitions
2. GLM decides whether to invoke tools and which ones to use
3. If invoked, tools perform operations and return structured results
4. GLM generates a response using the retrieved context
5. Sources are tracked separately via `ToolManager.get_last_sources()`

This approach allows the AI to intelligently decide when to search content vs. get structure, rather than forcing retrieval on every query.
