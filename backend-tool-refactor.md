Refactor @backend/ai_generator.py to support sequential tool calling where the AI model can make up to 2 tool calls in separate API rounds.

Current behavior:
- The model makes 1 tool call -> tool results are returned -> final response is generated.
- If the model requires another tool call after processing initial results, it is restricted (results in an incomplete or empty response).


Desired behavior:
- Each tool call should be a separate API request/response cycle where the model can reason about previous tool outputs before deciding the next step.
- Support complex queries requiring iterative steps, such as multi-part searches, comparisons, or cross-referencing information from different sources (e.g., courses/lessons).


Example flow:
1. User: "Search for a course that discusses the same topic as lesson 4 of couse X"
2. Model: get course outline for course X -> gets title of lesson 4
3. Model: uses the title to search for a course that discusses the same topic -> returns couse information
4. Model: Synthesizes all information into a final complete answer.


Requirements:
- Limit: Maximum 2 sequential tool-calling rounds per user query.
- Termination: Stop when: (a) 2 rounds are completed, (b) the model provides a final text response without tool requests, or (c) a tool execution error occurs.
- Context: Ensure the full conversation history (including previous tool calls and results) is preserved and sent in each subsequent API round.
- Error Handling: Handle tool execution failures gracefully without crashing the loop.


Notes:
- Update the system prompt in @backend/ai_generator.py
- Update the test @backend/tests/test_ai_generator.py
- Write tests that verify the external behavior (API calls made, tools executed, results returned) rather than internal state details


Use two parallel subagents to brainstorm possible plans. Do not implement any code.






这段提示词（Prompt）的核心目标是**升级 AI 后端逻辑，使其支持“多轮工具调用（Sequential Tool Calling）”**。

简单来说，就是让 Claude 不再只会“一锤子买卖”，而是具备“思考 $\rightarrow$ 搜一次 $\rightarrow$ 看结果 $\rightarrow$ 再搜一次 $\rightarrow$ 给答案”的连贯推理能力。

---

### 1. 核心含义解析

* **当前问题（Current behavior）：** 现在的系统太“死板”。Claude 只能调用一次工具，然后工具参数就会被移除，直接给用户回复。如果它发现第一次搜到的结果不够，想再搜一次，系统会报错或给空回复。
* **期望行为（Desired behavior）：** 允许 Claude 进行“思考循环”。它可以在看到第一个工具的返回结果后，基于这些信息决定是否需要进行第二次调用。
* **应用场景：** 处理复杂查询。例如：“找一个和课程 X 第 4 课主题相同的课程”。AI 必须先查“第 4 课是什么主题”，拿到主题后，再去搜“包含该主题的课程”。

### 2. 技术要求 (Requirements)

* **次数限制：** 每次用户提问最多允许 **2 轮** 连续调用（防止陷入死循环或消耗过多 Token）。
* **终止条件：** 满 2 轮、AI 不再需要工具、或工具调用出错时停止。
* **上下文保持：** 必须把第一轮的结果带入第二轮，AI 才知道刚才发生了什么。
* **测试要求：** 重点测试“外部表现”（调了几次 API、结果对不对），而不是代码内部的变量状态。

---

### 3. 双子代理（Subagents）方案头脑风暴

为了实现这个功能，我们让两个虚拟“子代理”从不同角度构思方案：

---

### 4. 总结与建议

这个提示词的作用是**将 AI 从“单步执行器”提升为“多步推理器”**。

**我接下来可以为您做的是：**

1. 为您草拟 `@backend/ai_generator.py` 中需要修改的**系统提示词（System Prompt）**，以引导 Claude 适应这两轮调用。
2. 为您设计测试用例的**伪代码**，模拟那两个步骤的搜索逻辑。

您希望我先从哪一部分开始？