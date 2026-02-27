"""Comprehensive tests for AIGenerator tool calling functionality"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from ai_generator import AIGenerator
import json


class TestAIGeneratorToolCalling:
    """Test suite for AIGenerator tool calling functionality"""

    # ========================================================================
    # Tool Format Conversion
    # ========================================================================

    def test_tool_format_conversion_single_tool(self):
        """Test converting a single Anthropic tool to GLM format"""
        generator = AIGenerator(api_key="test-key", model="glm-5")

        anthropic_tool = {
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }

        glm_tools = generator._convert_tools_to_glm_format([anthropic_tool])

        assert len(glm_tools) == 1
        assert glm_tools[0]["type"] == "function"
        assert "function" in glm_tools[0]

        glm_function = glm_tools[0]["function"]
        assert glm_function["name"] == "search_course_content"
        assert glm_function["description"] == "Search course materials"
        assert glm_function["parameters"] == anthropic_tool["input_schema"]

    def test_tool_format_conversion_multiple_tools(self):
        """Test converting multiple tools to GLM format"""
        generator = AIGenerator(api_key="test-key", model="glm-5")

        anthropic_tools = [
            {
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_course_outline",
                "description": "Get course outline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_title": {"type": "string"}
                    },
                    "required": ["course_title"]
                }
            }
        ]

        glm_tools = generator._convert_tools_to_glm_format(anthropic_tools)

        assert len(glm_tools) == 2
        assert glm_tools[0]["function"]["name"] == "search_course_content"
        assert glm_tools[1]["function"]["name"] == "get_course_outline"

    def test_tool_format_conversion_preserves_all_fields(self):
        """Test that all fields are preserved during conversion"""
        generator = AIGenerator(api_key="test-key", model="glm-5")

        anthropic_tool = {
            "name": "test_tool",
            "description": "Test description",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "First param"},
                    "param2": {"type": "integer", "description": "Second param"}
                },
                "required": ["param1"]
            }
        }

        glm_tools = generator._convert_tools_to_glm_format([anthropic_tool])

        glm_function = glm_tools[0]["function"]
        assert glm_function["name"] == "test_tool"
        assert glm_function["description"] == "Test description"
        assert glm_function["parameters"]["properties"]["param1"]["type"] == "string"
        assert glm_function["parameters"]["properties"]["param2"]["type"] == "integer"
        assert "param1" in glm_function["parameters"]["required"]

    # ========================================================================
    # Tool Invocation Tests
    # ========================================================================

    def test_invokes_search_tool_for_content_question(self, mock_ai_generator):
        """Test that AI invokes search_course_content for content-related questions"""
        # Create a mock response with tool call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "What is MCP protocol?"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock second response (after tool execution) - no more tool calls
        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "Based on the search results, MCP protocol is..."
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        # Mock tool manager
        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "MCP protocol is a communication standard..."

        # Execute
        result = mock_ai_generator.generate_response(
            query="What is MCP protocol?",
            tools=[{
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="What is MCP protocol?"
        )

    def test_invokes_outline_tool_for_structure_question(self, mock_ai_generator):
        """Test that AI invokes get_course_outline for structure questions"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_456"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_course_outline"
        mock_tool_call.function.arguments = '{"course_title": "MCP"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "The MCP course has 3 lessons..."
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Course: MCP\nLessons: 1, 2, 3"

        result = mock_ai_generator.generate_response(
            query="What lessons are in the MCP course?",
            tools=[{
                "name": "get_course_outline",
                "description": "Get course outline",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        mock_tool_manager.execute_tool.assert_called_once_with(
            "get_course_outline",
            course_title="MCP"
        )

    def test_does_not_invoke_tool_for_general_question(self, mock_ai_generator):
        """Test that AI doesn't invoke tools for general knowledge questions"""
        # Mock response without tool calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Paris is the capital of France."
        mock_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(return_value=mock_response)

        mock_tool_manager = MagicMock()

        result = mock_ai_generator.generate_response(
            query="What is the capital of France?",
            tools=[{
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Tool manager should not be called
        mock_tool_manager.execute_tool.assert_not_called()
        assert result == "Paris is the capital of France."

    # ========================================================================
    # Parameter Passing Tests
    # ========================================================================

    def test_passes_correct_parameters_basic_search(self, mock_ai_generator):
        """Test that correct parameters are passed for basic search"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_789"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "test query"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "Answer based on results"
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Search results..."

        mock_ai_generator.generate_response(
            query="test query",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Verify parameters passed correctly
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="test query"
        )

    def test_passes_correct_parameters_with_filters(self, mock_ai_generator):
        """Test that correct parameters are passed with course and lesson filters"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_101"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "protocol", "course_name": "MCP", "lesson_number": 2}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "Filtered answer"
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Filtered search results..."

        mock_ai_generator.generate_response(
            query="Tell me about protocol in lesson 2",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Verify all parameters were passed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="protocol",
            course_name="MCP",
            lesson_number=2
        )

    def test_passes_correct_parameters_outline(self, mock_ai_generator):
        """Test that course_title parameter is correctly passed for outline tool"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_202"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_course_outline"
        mock_tool_call.function.arguments = '{"course_title": "Introduction to RAG"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "Here is the outline"
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Course outline..."

        mock_ai_generator.generate_response(
            query="What's in the RAG course?",
            tools=[{
                "name": "get_course_outline",
                "description": "Get outline",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        mock_tool_manager.execute_tool.assert_called_once_with(
            "get_course_outline",
            course_title="Introduction to RAG"
        )

    # ========================================================================
    # Response Handling Tests
    # ========================================================================

    def test_handles_tool_results_correctly(self, mock_ai_generator):
        """Test that tool results are properly integrated into final response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_303"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "MCP"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = (
            "Based on the search results, MCP is a protocol "
            "that enables AI assistants to connect to external data sources."
        )
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = (
            "[Model Context Protocol - Lesson 1]\n"
            "MCP is a protocol for AI assistants."
        )

        result = mock_ai_generator.generate_response(
            query="What is MCP?",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should return the final AI response that incorporates tool results
        assert "MCP is a protocol" in result
        assert "external data sources" in result

    def test_handles_tool_results_with_empty_response(self, mock_ai_generator):
        """Test handling when tool returns no results"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_404"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "nonexistent topic"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "I couldn't find any information about that topic in the course materials."
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "No relevant content found."

        result = mock_ai_generator.generate_response(
            query="Tell me about nonexistent topic",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        assert "couldn't find" in result.lower() or "no information" in result.lower()

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_handles_tool_execution_failure(self, mock_ai_generator):
        """Test behavior when tool execution fails"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_500"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "test"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "I encountered an error searching the course materials."
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Error: Vector store connection failed"

        result = mock_ai_generator.generate_response(
            query="test query",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should handle error gracefully
        assert isinstance(result, str)

    def test_handles_invalid_json_in_tool_arguments(self, mock_ai_generator):
        """Test handling of malformed JSON in tool arguments"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_600"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        # Invalid JSON
        mock_tool_call.function.arguments = '{invalid json}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        # Final response explaining the error
        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "I encountered an error processing the tool arguments."
        mock_final_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response, mock_final_response]
        )

        mock_tool_manager = MagicMock()

        # Should catch JSON error and handle gracefully
        result = mock_ai_generator.generate_response(
            query="test",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should handle error gracefully, not raise exception
        assert isinstance(result, str)

    def test_handles_api_error(self, mock_ai_generator):
        """Test handling when GLM API call fails"""
        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=Exception("API Error: Rate limit exceeded")
        )

        mock_tool_manager = MagicMock()

        # Should propagate the error
        with pytest.raises(Exception, match="API Error"):
            mock_ai_generator.generate_response(
                query="test query",
                tools=[{
                    "name": "search_course_content",
                    "description": "Search",
                    "input_schema": {"type": "object", "properties": {}, "required": []}
                }],
                tool_manager=mock_tool_manager
            )

    # ========================================================================
    # Conversation History Tests
    # ========================================================================

    def test_includes_conversation_history(self, mock_ai_generator):
        """Test that conversation history is included in system prompt"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Follow-up answer"
        mock_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(return_value=mock_response)

        result = mock_ai_generator.generate_response(
            query="Follow-up question",
            conversation_history="User: What is MCP?\nAI: MCP is a protocol.",
            tools=None,
            tool_manager=None
        )

        # Verify the API was called
        mock_ai_generator.client.chat.completions.create.assert_called_once()

        # Check that history was included in the call
        call_args = mock_ai_generator.client.chat.completions.create.call_args
        messages = call_args[1]['messages']

        # Should have system and user messages
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert "Previous conversation" in messages[0]['content']
        assert "What is MCP?" in messages[0]['content']

    def test_without_conversation_history(self, mock_ai_generator):
        """Test that system prompt is correct without history"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Direct answer"
        mock_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(return_value=mock_response)

        result = mock_ai_generator.generate_response(
            query="New question",
            conversation_history=None,
            tools=None,
            tool_manager=None
        )

        call_args = mock_ai_generator.client.chat.completions.create.call_args
        messages = call_args[1]['messages']

        # System prompt should not include "Previous conversation"
        assert "Previous conversation" not in messages[0]['content']

    # ========================================================================
    # System Prompt Tests
    # ========================================================================

    def test_system_prompt_structure(self, mock_ai_generator):
        """Test that system prompt has proper structure"""
        assert hasattr(mock_ai_generator, 'SYSTEM_PROMPT')
        assert len(mock_ai_generator.SYSTEM_PROMPT) > 0
        assert "AI assistant" in mock_ai_generator.SYSTEM_PROMPT
        assert "tool" in mock_ai_generator.SYSTEM_PROMPT.lower()

    def test_base_api_parameters(self, mock_ai_generator):
        """Test that base API parameters are set correctly"""
        assert hasattr(mock_ai_generator, 'base_params')
        assert mock_ai_generator.base_params['model'] == 'glm-5'
        assert mock_ai_generator.base_params['temperature'] == 0
        assert 'max_tokens' in mock_ai_generator.base_params


# ============================================================================
# Sequential Tool Calling Tests
# ============================================================================

class TestSequentialToolCalling:
    """Test suite for sequential multi-round tool calling functionality"""

    def test_single_round_no_tools(self, mock_ai_generator):
        """Test Round 1 → text (no tools) - immediate termination"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Paris is the capital of France."
        mock_response.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(return_value=mock_response)

        result = mock_ai_generator.generate_response(
            query="What is the capital of France?",
            tools=[{
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=MagicMock()
        )

        # Should return direct text without any tool calls
        assert result == "Paris is the capital of France."
        mock_ai_generator.client.chat.completions.create.assert_called_once()

    def test_single_round_with_tools(self, mock_ai_generator):
        """Test Round 1 → tool → Round 2 → text (model declines second tool)"""
        # Round 1: Model calls tool
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_1"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "MCP protocol"}'
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call]

        # Round 2: Model returns text without calling another tool
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = "MCP protocol is a communication standard for AI assistants."
        mock_response_2.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_1, mock_response_2]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "MCP protocol enables AI assistants to connect to external data."

        result = mock_ai_generator.generate_response(
            query="What is MCP protocol?",
            tools=[{
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should execute tool once and return final answer
        mock_tool_manager.execute_tool.assert_called_once_with("search_course_content", query="MCP protocol")
        assert "MCP protocol" in result

    def test_two_rounds_with_tools(self, mock_ai_generator):
        """Test Round 1 → tool → Round 2 → tool → final text"""
        # Round 1: Model calls get_course_outline
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = None
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function.name = "get_course_outline"
        mock_tool_call_1.function.arguments = '{"course_title": "MCP"}'
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call_1]

        # Round 2: Model calls search_course_content based on outline
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = None
        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.type = "function"
        mock_tool_call_2.function.name = "search_course_content"
        mock_tool_call_2.function.arguments = '{"query": "Tools and Resources", "course_name": "MCP"}'
        mock_response_2.choices[0].message.tool_calls = [mock_tool_call_2]

        # Final: Model synthesizes answer
        mock_response_final = MagicMock()
        mock_response_final.choices = [MagicMock()]
        mock_response_final.choices[0].message.content = (
            "Lesson 3 of the MCP course covers Tools and Resources. "
            "It explains how MCP tools can be configured with parameters."
        )
        mock_response_final.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_1, mock_response_2, mock_response_final]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.side_effect = [
            # First tool result: course outline
            "Course: MCP Introduction\nLessons:\n  Lesson 1: Introduction\n  Lesson 2: Setup\n  Lesson 3: Tools and Resources",
            # Second tool result: search content
            "[MCP - Lesson 3]\nMCP tools can be configured with parameters. The AI decides when to invoke each tool."
        ]

        result = mock_ai_generator.generate_response(
            query="Get outline of MCP course, then tell me what lesson 3 covers",
            tools=[
                {
                    "name": "get_course_outline",
                    "description": "Get course outline",
                    "input_schema": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "search_course_content",
                    "description": "Search course materials",
                    "input_schema": {"type": "object", "properties": {}, "required": []}
                }
            ],
            tool_manager=mock_tool_manager
        )

        # Should execute both tools
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call("get_course_outline", course_title="MCP")
        mock_tool_manager.execute_tool.assert_any_call(
            "search_course_content",
            query="Tools and Resources",
            course_name="MCP"
        )
        assert "Lesson 3" in result

    def test_max_rounds_enforcement(self, mock_ai_generator):
        """Test that max rounds (2) is enforced - should make final call without tools"""
        # Round 1: Tool call
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = None
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function.name = "search_course_content"
        mock_tool_call_1.function.arguments = '{"query": "first"}'
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call_1]

        # Round 2: Another tool call
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = None
        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.type = "function"
        mock_tool_call_2.function.name = "search_course_content"
        mock_tool_call_2.function.arguments = '{"query": "second"}'
        mock_response_2.choices[0].message.tool_calls = [mock_tool_call_2]

        # Final: Should NOT have tools available (max rounds reached)
        mock_response_final = MagicMock()
        mock_response_final.choices = [MagicMock()]
        mock_response_final.choices[0].message.content = "Synthesized answer after 2 rounds of tools."
        mock_response_final.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_1, mock_response_2, mock_response_final]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.side_effect = [
            "First result",
            "Second result"
        ]

        result = mock_ai_generator.generate_response(
            query="Test max rounds",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should make exactly 3 API calls: 2 with tools, 1 final without tools
        assert mock_ai_generator.client.chat.completions.create.call_count == 3
        # Should execute both tools
        assert mock_tool_manager.execute_tool.call_count == 2
        assert "Synthesized answer" in result

    def test_tool_error_in_round_1(self, mock_ai_generator):
        """Test tool execution error in Round 1 - graceful handling"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_error"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "search_course_content"
        mock_tool_call.function.arguments = '{"query": "test"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_ai_generator.client.chat.completions.create = MagicMock(return_value=mock_response)

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.side_effect = Exception("Vector store connection failed")

        # Final response explaining error
        mock_error_response = MagicMock()
        mock_error_response.choices = [MagicMock()]
        mock_error_response.choices[0].message.content = "I encountered an error searching the course materials."
        mock_ai_generator.client.chat.completions.create.side_effect = [
            mock_response,
            mock_error_response
        ]

        result = mock_ai_generator.generate_response(
            query="test query",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should handle error gracefully
        assert isinstance(result, str)
        assert mock_ai_generator.client.chat.completions.create.call_count == 2

    def test_empty_results_continues(self, mock_ai_generator):
        """Test that empty tool results are valid and don't cause errors"""
        # Round 1: Tool returns empty results
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = None
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function.name = "search_course_content"
        mock_tool_call_1.function.arguments = '{"query": "nonexistent"}'
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call_1]

        # Round 2: Model responds to empty results
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = "I couldn't find any information about that topic."
        mock_response_2.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_1, mock_response_2]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "No relevant content found."

        result = mock_ai_generator.generate_response(
            query="Tell me about nonexistent topic",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should handle empty results gracefully
        assert "couldn't find" in result.lower() or "no information" in result.lower()

    def test_same_tool_twice(self, mock_ai_generator):
        """Test that calling the same tool twice in sequence is valid"""
        # Round 1: First search
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = None
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function.name = "search_course_content"
        mock_tool_call_1.function.arguments = '{"query": "MCP protocol"}'
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call_1]

        # Round 2: Second search with different query
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = None
        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.type = "function"
        mock_tool_call_2.function.name = "search_course_content"
        mock_tool_call_2.function.arguments = '{"query": "MCP tools"}'
        mock_response_2.choices[0].message.tool_calls = [mock_tool_call_2]

        # Final response
        mock_response_final = MagicMock()
        mock_response_final.choices = [MagicMock()]
        mock_response_final.choices[0].message.content = (
            "MCP protocol is a communication standard, and MCP tools are functions "
            "that perform specific actions."
        )
        mock_response_final.choices[0].message.tool_calls = None

        mock_ai_generator.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_1, mock_response_2, mock_response_final]
        )

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.side_effect = [
            "MCP protocol is a communication standard.",
            "MCP tools are functions that perform specific actions."
        ]

        result = mock_ai_generator.generate_response(
            query="Tell me about MCP protocol and tools",
            tools=[{
                "name": "search_course_content",
                "description": "Search",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            }],
            tool_manager=mock_tool_manager
        )

        # Should call same tool twice
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="MCP protocol")
        mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="MCP tools")
