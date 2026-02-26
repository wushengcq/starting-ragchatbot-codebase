from zhipuai import ZhipuAI
from typing import List, Optional, Dict, Any
import json

class AIGenerator:
    """Handles interactions with BigModel's GLM API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Available Tools:
1. **get_course_outline** - Use for questions about course structure, lesson lists, and course links
   - Input: Course title (full or partial)
   - Output: Course title, course link, instructor, and complete lesson list with numbers and titles

2. **search_course_content** - Use for questions about specific course content or detailed materials
   - Input: Search query, optional course name, optional lesson number
   - Output: Relevant content excerpts with sources

Tool Usage Guidelines:
- **Course outline questions** (e.g., "What's covered in X course?", "List lessons in X"): Use get_course_outline
- **Content questions** (e.g., "What does X say about Y?", "Explain topic from lesson Z"): Use search_course_content
- **One tool call per query maximum**
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **For course outline responses**: Present the course title, course link, instructor, and lessons with their numbers explicitly shown
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the tool results" or similar phrases

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = ZhipuAI(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
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
            {"role": "user", "content": query}
        ]

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": messages
        }

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
            glm_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return glm_tools
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Add AI's tool use response
        assistant_message = initial_response.choices[0].message

        # Convert tool_calls to dict format for JSON serialization
        tool_calls_dict = []
        if assistant_message.tool_calls:
            for tc in assistant_message.tool_calls:
                tool_calls_dict.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": tool_calls_dict
        })

        # Execute all tool calls and collect results
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            # Parse JSON string to dict
            function_args = json.loads(tool_call.function.arguments)

            tool_result = tool_manager.execute_tool(function_name, **function_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        # Prepare final API call without tools
        # Note: system message is already in messages array from base_params
        final_params = {
            **self.base_params,
            "messages": messages
        }

        # Get final response
        final_response = self.client.chat.completions.create(**final_params)
        return final_response.choices[0].message.content