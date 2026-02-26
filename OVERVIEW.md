# RAG Chatbot Codebase Overview

---

## 📁 Project Structure

```
starting-ragchatbot-codebase/
├── backend/                    # Python backend (FastAPI)
│   ├── ai_generator.py        # ZhipuAI GLM integration
│   ├── app.py                # FastAPI entry point
│   ├── config.py             # Configuration
│   ├── document_processor.py  # Document parsing & chunking
│   ├── models.py             # Data models
│   ├── rag_system.py         # Main orchestrator
│   ├── search_tools.py       # AI tool definitions
│   ├── session_manager.py    # Conversation state
│   └── vector_store.py       # ChromaDB wrapper
├── frontend/                  # Vanilla JS frontend
│   ├── index.html
│   ├── style.css
│   └── script.js
├── docs/                     # Course materials (4 courses)
├── pyproject.toml           # Python dependencies
└── run.sh                   # Dev server launcher
```

---

## 🏗️ Architecture

### System Flow

```
User Query → Frontend → FastAPI → RAG System
                                     ↓
                              AI Generator
                                     ↓
                    ┌────────────────┴────────────────┐
                    ↓                                 ↓
            Needs Search?                      Direct Answer
                    ↓                                 ↓
          Search Tools → Vector Store          Generate Response
                    ↓                                 ↓
          Retrieve Context → Generate Response → User
```

---

## 🔧 Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **RAG System** | `rag_system.py` | Central orchestrator, coordinates all components |
| **Vector Store** | `vector_store.py` | ChromaDB wrapper with 2 collections (metadata + content) |
| **AI Generator** | `ai_generator.py` | ZhipuAI GLM API integration, tool calling |
| **Document Processor** | `document_processor.py` | Parses course docs, creates chunks (800 chars) |
| **Search Tools** | `search_tools.py` | Tool definitions for AI-invoked search |
| **Session Manager** | `session_manager.py` | Multi-turn conversation context |
| **FastAPI App** | `app.py` | REST API + static file serving |

---

## 🔑 Key Technologies

**Backend:**
- FastAPI (Python web framework)
- ChromaDB (vector database)
- sentence-transformers (embeddings: all-MiniLM-L6-v2)
- ZhipuAI GLM (Chinese AI model)

**Frontend:**
- Vanilla JavaScript (no frameworks)
- Marked.js (markdown rendering)

---

## 📊 Data Flow

### Document Ingestion (on startup)
1. Load `.txt` files from `/docs/`
2. Extract course metadata (title, instructor, lessons)
3. Chunk content with overlap (800 chars, 100 overlap)
4. Store in ChromaDB:
   - `course_catalog` → course discovery
   - `course_content` → detailed content

### Query Processing
1. User sends query + session_id
2. AI decides: needs search or direct answer?
3. If search: query vector store → get relevant chunks
4. AI generates response using retrieved context
5. Return answer + sources

---

## ⚙️ Configuration

**`config.py`** key settings:
- `BIGMODEL_MODEL`: "glm-5" (AI model)
- `CHUNK_SIZE`: 800 (text chunk size)
- `CHUNK_OVERLAP`: 100 (overlap between chunks)
- `MAX_RESULTS`: 5 (search results)
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2"

**Environment:**
- `.env` → `BIGMODEL_API_KEY` (required)

---

## 🎯 Key Features

1. **Tool-Based AI**: AI decides when to search (not forced)
2. **Dual Vector Stores**: Metadata + content separately
3. **Conversation Memory**: Multi-turn context (configurable)
4. **Smart Course Matching**: Fuzzy name resolution
5. **Source Attribution**: Returns source references
6. **Error Logging**: Full tracebacks for debugging

---

## 🚀 Quick Start

```bash
# Install dependencies
uv sync

# Set API key in .env
BIGMODEL_API_KEY=your.key.here

# Run server
./run.sh
```

Access at: http://localhost:8000

---

## 📝 API Endpoints

### POST /api/query
Process user queries and return AI-generated responses with sources.

**Request:**
```json
{
  "query": "What is covered in the first lesson?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "The first lesson covers...",
  "sources": ["Course: Python Basics - Lesson 0"],
  "session_id": "session-id"
}
```

### GET /api/courses
Get course statistics and list of available courses.

**Response:**
```json
{
  "total_courses": 4,
  "course_titles": ["Python Basics", "Advanced Python", ...]
}
```

---

## 📚 Document Format

Course documents in `/docs/` follow this structured format:

```
Course Title: [Course Title]
Course Link: [URL]
Course Instructor: [Instructor Name]

Lesson 0: Introduction
Lesson Link: [URL]
[Lesson content...]

Lesson 1: Next Topic
Lesson Link: [URL]
[Lesson content...]
```

Documents are automatically loaded on startup. Duplicate courses (by title) are skipped.

---

## 🔍 How Tool-Based Search Works

The system uses Claude's function calling capabilities to give the AI control over when to search:

1. AI receives user query + available tool definitions
2. Claude decides whether to invoke `search_course_content` tool
3. If invoked, the tool performs semantic search and returns results
4. Claude generates a response using the retrieved context
5. Sources are tracked separately for attribution

This approach allows the AI to intelligently decide when search is needed, rather than forcing retrieval on every query.

---

## 🐛 Debugging

The application includes detailed error logging. To see full error tracebacks:

1. Check the server console where `./run.sh` is running
2. Errors are logged with timestamps and full stack traces
3. Use the test script to verify API key: `uv run python test_api_key.py`

---

## 📦 Dependencies

Core dependencies defined in `pyproject.toml`:
- `fastapi==0.116.1` - Web framework
- `chromadb==1.0.15` - Vector database
- `sentence-transformers==5.0.0` - Text embeddings
- `zhipuai>=2.0.0` - AI model integration
- `python-dotenv==1.1.1` - Environment configuration
- `uvicorn==0.35.0` - ASGI server

---

## 🔄 Development Workflow

```bash
# Start development server
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000

# Test API key
uv run python test_api_key.py

# Install new dependencies
uv sync
```

---

## 📖 Additional Resources

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Project Instructions**: See `CLAUDE.md` for development guidance
- **Environment Template**: See `.env.example` for configuration options
