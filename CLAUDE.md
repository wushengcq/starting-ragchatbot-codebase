# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system for querying course materials. Users can ask questions about educational content and receive intelligent, context-aware responses powered by semantic search and Claude AI.

**Tech Stack**: Python 3.13+ (FastAPI backend), vanilla JavaScript (frontend), ChromaDB (vector store), Anthropic Claude (AI generation)

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
- `ANTHROPIC_API_KEY` in `.env` file

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

**`search_tools.py`** - Implements tool-based AI integration. The `CourseSearchTool` provides a structured search interface (`search_course_content`) that Claude can invoke. This gives the AI control over when to search, rather than forcing retrieval on every query.

**`vector_store.py`** - ChromaDB wrapper managing two collections:
- `course_metadata` - For semantic course discovery
- `course_content` - For detailed lesson content retrieval

**`document_processor.py`** - Parses structured text files. Extracts course metadata (title, instructor, lessons) and creates overlapping text chunks (default: 800 chars with 100 char overlap).

**`ai_generator.py`** - Anthropic Claude integration. Handles tool calling and response generation with conversation history.

**`session_manager.py`** - Manages conversation state and history for multi-turn context.

**`app.py`** - FastAPI application with two main endpoints:
- `POST /api/query` - Process user queries
- `GET /api/courses` - Get course statistics

Auto-loads documents from `/docs/` on startup via `startup_event()`.

**`config.py`** - Centralized configuration using dataclasses. Key settings:
- `CHUNK_SIZE`: 800 (text chunk size)
- `CHUNK_OVERLAP`: 100 (characters between chunks)
- `MAX_RESULTS`: 5 (search results to return)
- `MAX_HISTORY`: 2 (conversation turns to remember)
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2"
- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"

### Frontend

Vanilla JavaScript in `/frontend/`:
- `index.html` - Single-page application structure
- `style.css` - Responsive styling with sidebar layout
- `script.js` - API client for querying backend

Static files are served directly by FastAPI with no-cache headers for development.

## Document Format

Course documents in `/docs/` follow a structured text format:

```
Title: [Course Title]
Instructor: [Instructor Name]

[Lesson content...]
```

Documents are automatically loaded on startup. The system tracks existing courses by title and skips duplicates.

## Tool-Based AI Integration

The system uses Claude's function calling capabilities. When processing a query:

1. The AI receives the user query + available tool definitions
2. Claude decides whether to invoke `search_course_content` tool
3. If invoked, the tool performs semantic search and returns results
4. Claude generates a response using the retrieved context
5. Sources are tracked separately via `ToolManager.get_last_sources()`

This approach allows the AI to intelligently decide when search is needed, rather than forcing retrieval on every query.
