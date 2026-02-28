import json
from typing import Any, Dict, List, Optional

from zhipuai import ZhipuAI


class AIGenerator:
    """Handles interactions with BigModel's GLM API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    # fmt: off
    SYSTEM_PROMPT = (
        "You are an AI assistant specialized in course materials and educational content "
        "with access to tools for course information.\n\n"
        "Available Tools:\n"
        "1. **get_course_outline** - Use for questions about course structure, lesson lists, "
        "and course links\n"
        "   - Input: Course title (full or partial)\n"
        "   - Output: Course title, course link, instructor, and complete lesson list with "
        "numbers and titles\n\n"
        "2. **search_course_content** - Use for questions about specific course content or "
        "detailed materials\n"
        "   - Input: Search query, optional course name, optional lesson number\n"
        "   - Output: Relevant content excerpts with sources\n\n"
        "Tool Usage Guidelines:\n"
        "- **Course outline questions** (e.g., \"What's covered in X course?\", "
        "\"List lessons in X\"): Use get_course_outline\n"
        "- **Content questions** (e.g., \"What does X say about Y?\", "
        "\"Explain topic from lesson Z\"): Use search_course_content\n"
        "- **Multi-round capability**: You can make up to 2 sequential tool calls to answer "
        "complex questions\n"
        "  - Example: First get course outline to find a lesson title, then search for "
        "content about that topic\n"
        "  - Use each round to build on previous tool results\n"
        "- If a tool yields no results, state this clearly without offering alternatives\n\n"
        "Response Protocol:\n"
        "- **General knowledge questions**: Answer using existing knowledge without tools\n"
        "- **Course-specific questions**: Use appropriate tool(s), then synthesize the "
        "information\n"
        "- **For course outline responses**: Present the course title, course link, "
        "instructor, and lessons with their numbers explicitly shown\n"
        "- **No meta-commentary**:\n"
        " - Provide direct answers only — no reasoning process, tool explanations, or "
        "question-type analysis\n"
        " - Do not mention \"based on the tool results\" or similar phrases\n\n"
        "All responses must be:\n"
        "1. **Brief, Concise and focused** - Get to the point quickly\n"
        "2. **Educational** - Maintain instructional value\n"
        "3. **Clear** - Use accessible language\n"
        "4. **Example-supported** - Include relevant examples when they aid understanding\n"
        "5. **Comprehensive** - When using multiple tools, synthesize information from all "
        "tool results\n\n"
        "Provide only the direct answer to what was asked."
    )
    # fmt: on

    def __init__(self, api_key: str, model: str):
        self.client = ZhipuAI(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare messages array with system message (ZhipuAI/GLM format)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
        ]

        # Prepare API call parameters efficiently
        api_params = {**self.base_params, "messages": messages}

        # Add tools if available (convert to GLM format)
        if tools:
            api_params["tools"] = self._convert_tools_to_glm_format(tools)
            api_params["tool_choice"] = "auto"

        # Get response from GLM
        response = self.client.chat.completions.create(**api_params)

        # Handle tool execution if needed
        if response.choices[0].message.tool_calls and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)

        # Return direct response
        return response.choices[0].message.content

    def _convert_tools_to_glm_format(self, anthropic_tools: List) -> List[Dict]:
        """Convert Anthropic tool format to GLM/OpenAI format"""
        glm_tools = []
        for tool in anthropic_tools:
            glm_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"],
                    },
                }
            )
        return glm_tools

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls with support for up to 2 sequential rounds.

        Loop structure:
        for round_number in range(1, MAX_ROUNDS + 1):
            1. Check if response has tool_calls
               - If no: Extract and return text
               - If yes: Continue to step 2

            2. Execute tools from response
               - Try: Execute all tools, append results to messages
               - Except: Append error message, break loop

            3. Make follow-up API call
               - Tools still enabled (model can call another tool)
               - Append new assistant message + tool results

            4. Check if max rounds reached
               - If round_number == MAX_ROUNDS:
                 - Make final API call WITHOUT tools
                 - Return final text
               - Else: Continue to next iteration

        Args:
            initial_response: First API response
            base_params: Initial API parameters
            tool_manager: Tool execution manager

        Returns:
            Final response text
        """
        from config import config

        messages = base_params["messages"].copy()
        response = initial_response

        for round_number in range(1, config.MAX_TOOL_ROUNDS + 1):
            # Check if model wants to use tools
            if not response.choices[0].message.tool_calls:
                return response.choices[0].message.content

            # Execute tools
            assistant_message = response.choices[0].message

            # Build assistant message with tool_calls
            tool_calls_dict = []
            if assistant_message.tool_calls:
                for tc in assistant_message.tool_calls:
                    tool_calls_dict.append(
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    )

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": tool_calls_dict,
                }
            )

            # Execute each tool and append results
            for tool_call in assistant_message.tool_calls:
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    tool_result = tool_manager.execute_tool(
                        tool_call.function.name, **function_args
                    )
                    messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
                    )
                except Exception as e:
                    # Tool execution error - add error message
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {str(e)}",
                        }
                    )
                    # Make final API call to handle error gracefully
                    final_params = {**self.base_params, "messages": messages}
                    final_response = self.client.chat.completions.create(**final_params)
                    return final_response.choices[0].message.content

            # Check if this was the last allowed round
            if round_number >= config.MAX_TOOL_ROUNDS:
                # Make final API call WITHOUT tools to get answer
                final_params = {**self.base_params, "messages": messages}
                final_response = self.client.chat.completions.create(**final_params)
                return final_response.choices[0].message.content

            # Make next API call WITH tools (for potential second tool use)
            api_params = {
                **self.base_params,
                "messages": messages,
                "tools": base_params.get("tools"),
                "tool_choice": "auto",
            }
            response = self.client.chat.completions.create(**api_params)

        # Should never reach here, but return last response if we do
        return response.choices[0].message.content
