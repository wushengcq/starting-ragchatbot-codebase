# Notes

## Prompt

+ give me an overview of the codebase
+ how are these documents processed
+ trace the process of handling a user's query from frontend to backend
+ draw a diagram that illustrates the flow
+ how do I run this application?
+ explain what is in the codebase
+ add and commit these changes
+ these links are hard to read, can you make this more visually appealing
+ Add a '+ NEW CHAT' button to the left sidebar above the courses section. When clicked, it should:
  - Clear the current converstaion in the chat window
  - Start a new session without page reload
  - Handle proper cleanup on both @fronted and @backend
  - Match the styling of existing sections(Courses, Try asking) - same font size, color, and uppercase formatting
+ Using the playwright MCP server visit 127.0.0.1:8000 and view the new chat button. I want that buttong to look the same as the other links below for Courses and Try Asking. Make sure this is left aligned and that the border is removed
+ Using the playwright MCP server visit 127.0.0.1:8000 and view the Theme Toggle Button, make sure it work correctly for theme switch and smooth animation.

+ In @backend/search_tools.py, add a second tool alongside the existing content-related tool. This new tool should handle course outline queries.
  - Functionality:
    - Input: Course title.
    - Output: Course title, course link, and complete lesson list.
    - For each lesson: lesson number, lesson title.
  - Data source: Course metadata collection of the vector store.
  - Update the system prompt in @backend/ai_generator so that the course title, course link, the number and title of each lesson are all returned to address an outline-related queries.
  - Make usre that the new tool is registered in the system.
+ I've updated several files. Please scan the project structure and my recent changes, then update CLAUDE.md to reflect the current code structure, modules, functionalities, workflows, algrithms, test suites and coding patterns.
+ The RAG chatbot return 'Query failed' for any content-related questions. I need you to:
  1. Write tests to evaluate the outputs of the execute method of the CourseSearchTool in @backend/search_tools.py
  2. Write tests to evaluate if @backend/ai_generator.py correctly calls for the CourseSearchTool
  3. Write tests to evaluate how the RAG system is handling the content-query reloated questions.

  Save the tests in a tests folder within @backend. Run thoso test against the current system to identify which components are failing. Propose fixes based on what the tests reveal is broken.

+ One search per query maximum
  - 翻译： 每次提问最多只能进行一次搜索。
  - 意思： 限制 AI 的调用频率，即在你每问一个问题时，它只能“联网搜一次”，不能连续刷屏搜索。

+ If initial search results are insufficient, you may search again with different parameter.
  - 翻译： 如果初步搜索结果不足（无法解决问题），你可以更换参数（关键词）再次尝试搜索。
  - 意思： 这赋予了 AI 一定的灵活性。如果第一次搜到的信息太少或不相关，它可以调整搜索词再试一次，以确保获取有用的信息。

+ Synthesize search results into accurate, fact-baseed response.
  - 翻译： 将搜索结果综合整理为准确、基于事实的回答。
  - 意思： 要求 AI 不要直接“搬运”网页内容，而是要对搜到的多方信息进行逻辑汇总，并确保回答内容是真实可靠的，而不是凭空捏造。

+ If search yields on results. state this clearly without offering alternatives.
  - 翻译： 如果搜索没有结果，请明确说明，不要提供替代方案。
  - 意思： 这是一条非常严格的指令。如果搜不到信息，AI 必须老实承认“没搜到”，而不允许它根据猜测去推荐一些“可能相关”但未经证实的东西，防止误导用户。


+ Toggle Button Design
  - Create a toggle button that fits the existing design aesthetic
  - Position it in the top-right
  - Use an icon-based design (sun/moon icons or similar)
  - Smooth translation animation when toggling
  - Button should be accessible and keyboard-navigable

+ Add essential code quality tools to the development workflow. Set up Black for automatic code formatting. Add proper formatting consistency throughout the codebase and create development scripts for running quality checks.
  
+ Use the git merge command to merge in all of the worktrees in the .trees folder and fix any conflicts if there are any.

+ Stage all modified files and commit them with a concise, imperative-style message that explains the 'why' behind the changes.

## CLAUDE.md files

There are three common locations to store CLAUDE related md file.

+ **CLAUDE.md**
    + Generated with /init
    + Commit to source control
    + Sheared with other engineers
    + Location: project directory

+ **CLAUDE.local.md**
    + Not shared with other engineers
    + Contains personal instructions and customizations for Claude
    + Location: project directory

+ **~/.claude/CLAUDE.md**
    + Used with all project on your machine
    + Contains instructions that you want Claude to follow on all projects
    + Location: .claude folder stored in you home directory

## Useful command

+ /init     create a CLAUDE.md file
+ /help     list all the slash command
+ /clear    clear conversation history and free up context
+ /compact  clear conversation history but keep a summary in context. Optional: /compact [instructions for summarization]


## Skills

+ 第一种方法，在开始添加功能前，先定位需要修改的文件。这个可以让claude自己来确定，但如果能人为标记要修改的文件（使用@符号来标记），那将提高效率。
+ 第二种方法，使用方案计划模式（Planning mode）。进入计划模式（按两次 Shift+Tab）

## Resources

* **DeepLearning.AI - Claude Code**

    https://learn.deeplearning.ai/courses/claude-code-a-highly-agentic-coding-assistant/lesson/zzhtb/adding-features

* **Bilibili - 【吴恩达】2025年公认最好的【Claude Code】教程**

    https://www.bilibili.com/video/BV1wUpWz7EZk


## Install MCP

### Playwright 

```shell
export ALL_PROXY=socks5://127.0.0.1:7890

npx playwright install chromium
```