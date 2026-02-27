# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个检索增强生成（RAG）系统，用于查询课程材料。用户可以就教育内容提出问题，并通过语义搜索和 GLM AI 获得智能的、上下文相关的响应。

**技术栈**：Python 3.13+（FastAPI 后端）、原生 JavaScript（前端）、ChromaDB（向量存储）、BigModel GLM-5（AI 生成）

## 开发命令

```bash
# 安装依赖
uv sync

# 启动开发服务器（推荐）
./run.sh

# 手动启动
cd backend && uv run uvicorn app:app --reload --port 8000
```

**前提条件**：
- Python 3.13+
- uv 包管理器
- `.env` 文件中的 `BIGMODEL_API_KEY`（BigModel GLM API 密钥）

**服务器端点**：
- Web 界面：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

## 架构

系统遵循模块化管道架构。每个组件都有单一职责，由中央 RAG 系统协调。

### 核心管道流程

1. **文档摄取**：启动时解析、分块和向量化 `/docs/` 中的课程文档
2. **向量存储**：两个 ChromaDB 集合分别存储课程元数据和内容块
3. **查询处理**：使用对话上下文处理用户查询
4. **基于工具的搜索**：AI 根据查询决定何时调用搜索工具
5. **AI 生成**：AI 使用检索到的上下文生成响应
6. **响应传递**：返回带有来源归因的答案

### 关键后端组件

**`rag_system.py`** - 中央协调器。初始化所有组件并协调流程。关键方法：
- `add_course_folder()` - 启动时从 `/docs/` 加载文档
- `query()` - 使用对话上下文处理用户查询

**`search_tools.py`** - 实现基于工具的 AI 集成，包含两个工具：
- `CourseSearchTool`：提供 `search_course_content` 用于搜索课程材料，支持可选过滤器（course_name、lesson_name）
- `CourseOutlineTool`：提供 `get_course_outline` 用于检索课程结构和课程列表

这使得 AI 可以控制何时搜索以及何时获取课程结构，而不是在每次查询时强制检索。

**`vector_store.py`** - ChromaDB 包装器，管理两个集合：
- `course_catalog` - 用于语义课程发现
- `course_content` - 用于详细课程内容检索

**`document_processor.py`** - 解析结构化文本文件。提取课程元数据（标题、讲师、课程）并创建重叠文本块（默认：800 字符，100 字符重叠）。

**`ai_generator.py`** - BigModel GLM 集成。使用 glm-5 模型处理工具调用和带有对话历史的响应生成。

**`session_manager.py`** - 管理对话状态和历史记录以支持多轮上下文。

**`app.py`** - FastAPI 应用程序，具有三个主要端点：
- `POST /api/query` - 处理用户查询
- `GET /api/courses` - 获取课程统计信息
- `POST /api/clear-session` - 清除对话会话历史

通过 `startup_event()` 在启动时自动从 `/docs/` 加载文档。

**`config.py`** - 使用数据类的集中配置。关键设置：
- `CHUNK_SIZE`：800（文本块大小）
- `CHUNK_OVERLAP`：100（块之间的字符数）
- `MAX_RESULTS`：5（返回的搜索结果数）
- `MAX_HISTORY`：2（记住的对话轮次）
- `EMBEDDING_MODEL`："all-MiniLM-L6-v2"
- `BIGMODEL_MODEL`："glm-5"

### 前端

`/frontend/` 中的原生 JavaScript：
- `index.html` - 单页应用程序结构
- `style.css` - 带有侧边栏布局的响应式样式
- `script.js` - 用于查询后端的 API 客户端

**功能**：
- 新建聊天按钮，用于启动新的对话会话
- 可点击的来源引用，直接链接到课程视频
- 侧边栏中显示的课程统计信息
- 实时查询/响应流式传输

静态文件由 FastAPI 直接提供服务，开发环境使用无缓存头。

## 文档格式

`/docs/` 中的课程文档遵循结构化文本格式：

```
Title: [课程标题]
Instructor: [讲师姓名]
Course Link: [课程 URL]

## [第 1 课名称]
Lesson Link: [课程 URL]

[课程内容...]

## [第 2 课名称]
Lesson Link: [课程 URL]

[课程内容...]
```

**字段**：
- `Title` - 课程名称（必需）
- `Instructor` - 讲师姓名（必需）
- `Course Link` - 课程页面的 URL（可选）
- `## [课程名称]` - 课程标题，下方带有链接（必需）

文档在启动时自动加载。系统按标题跟踪现有课程并跳过重复项。

## 基于工具的 AI 集成

系统使用 GLM 的函数调用功能，提供两个工具：

**1. CourseSearchTool (`search_course_content`)**：
- 使用语义相似性搜索课程内容
- 可选过滤器：`course_name`、`lesson_name`
- 返回带有元数据的相关块（课程、课程、位置）

**2. CourseOutlineTool (`get_course_outline`)**：
- 检索课程结构和课程列表
- 不需要参数
- 返回有组织的课程/课程层次结构

处理查询时：

1. AI 接收用户查询 + 可用的工具定义
2. GLM 决定是否调用工具以及使用哪些工具
3. 如果调用，工具执行操作并返回结构化结果
4. GLM 使用检索到的上下文生成响应
5. 来源通过 `ToolManager.get_last_sources()` 单独跟踪

这种方法使 AI 能够智能地决定何时搜索内容与获取结构，而不是在每次查询时强制检索。
