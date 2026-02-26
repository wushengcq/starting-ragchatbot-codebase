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
+ In @backend/search_tools.py, add a second tool alongside the existing content-related tool. This new tool should handle course outline queries.
  - Functionality:
    - Input: Course title.
    - Output: Course title, course link, and complete lesson list.
    - For each lesson: lesson number, lesson title.
  - Data source: Course metadata collection of the vector store.
  - Update the system prompt in @backend/ai_generator so that the course title, course link, the number and title of each lesson are all returned to address an outline-related queries.
  - Make usre that the new tool is registered in the system.


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