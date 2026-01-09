# -*- coding: utf-8 -*-

"""
Unit tests for converters_core module.

Tests for shared conversion logic used by both OpenAI and Anthropic adapters:
- Text content extraction
- Message merging
- JSON Schema sanitization
- Tool processing
- Thinking tag injection
"""

import pytest
from unittest.mock import patch

from kiro.converters_core import (
    extract_text_content,
    merge_adjacent_messages,
    ensure_assistant_before_tool_results,
    build_kiro_history,
    process_tools_with_long_descriptions,
    inject_thinking_tags,
    extract_tool_results_from_content,
    extract_tool_uses_from_message,
    sanitize_json_schema,
    convert_tools_to_kiro_format,
    convert_tool_results_to_kiro_format,
    UnifiedMessage,
    UnifiedTool,
)


# ==================================================================================================
# Tests for extract_text_content
# ==================================================================================================

class TestExtractTextContent:
    """Tests for extract_text_content function."""
    
    def test_extracts_from_string(self):
        """
        What it does: Verifies text extraction from a string.
        Purpose: Ensure string is returned as-is.
        """
        print("Setup: Simple string...")
        content = "Hello, World!"
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello, World!', Got '{result}'")
        assert result == "Hello, World!"
    
    def test_extracts_from_none(self):
        """
        What it does: Verifies None handling.
        Purpose: Ensure None returns empty string.
        """
        print("Setup: None...")
        
        print("Action: Extracting text...")
        result = extract_text_content(None)
        
        print(f"Comparing result: Expected '', Got '{result}'")
        assert result == ""
    
    def test_extracts_from_list_with_text_type(self):
        """
        What it does: Verifies extraction from list with type=text.
        Purpose: Ensure multimodal format is handled.
        """
        print("Setup: List with type=text...")
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": " World"}
        ]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_list_with_text_key(self):
        """
        What it does: Verifies extraction from list with text key.
        Purpose: Ensure alternative format is handled.
        """
        print("Setup: List with text key...")
        content = [{"text": "Hello"}, {"text": " World"}]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_list_with_strings(self):
        """
        What it does: Verifies extraction from list of strings.
        Purpose: Ensure string list is concatenated.
        """
        print("Setup: List of strings...")
        content = ["Hello", " ", "World"]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_mixed_list(self):
        """
        What it does: Verifies extraction from mixed list.
        Purpose: Ensure different formats in one list are handled.
        """
        print("Setup: Mixed list...")
        content = [
            {"type": "text", "text": "Part1"},
            "Part2",
            {"text": "Part3"}
        ]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Part1Part2Part3', Got '{result}'")
        assert result == "Part1Part2Part3"
    
    def test_converts_other_types_to_string(self):
        """
        What it does: Verifies conversion of other types to string.
        Purpose: Ensure numbers and other types are converted.
        """
        print("Setup: Number...")
        content = 42
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected '42', Got '{result}'")
        assert result == "42"
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list returns empty string.
        """
        print("Setup: Empty list...")
        content = []
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected '', Got '{result}'")
        assert result == ""


# ==================================================================================================
# Tests for merge_adjacent_messages
# ==================================================================================================

class TestMergeAdjacentMessages:
    """Tests for merge_adjacent_messages function using UnifiedMessage."""
    
    def test_merges_adjacent_user_messages(self):
        """
        What it does: Verifies merging of adjacent user messages.
        Purpose: Ensure messages with the same role are merged.
        """
        print("Setup: Two consecutive user messages...")
        messages = [
            UnifiedMessage(role="user", content="Hello"),
            UnifiedMessage(role="user", content="World")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert "Hello" in result[0].content
        assert "World" in result[0].content
    
    def test_preserves_alternating_messages(self):
        """
        What it does: Verifies preservation of alternating messages.
        Purpose: Ensure different roles are not merged.
        """
        print("Setup: Alternating messages...")
        messages = [
            UnifiedMessage(role="user", content="Hello"),
            UnifiedMessage(role="assistant", content="Hi"),
            UnifiedMessage(role="user", content="How are you?")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list doesn't cause errors.
        """
        print("Setup: Empty list...")
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages([])
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_handles_single_message(self):
        """
        What it does: Verifies single message handling.
        Purpose: Ensure single message is returned as-is.
        """
        print("Setup: Single message...")
        messages = [UnifiedMessage(role="user", content="Hello")]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].content == "Hello"
    
    def test_merges_multiple_adjacent_groups(self):
        """
        What it does: Verifies merging of multiple groups.
        Purpose: Ensure multiple groups of adjacent messages are merged.
        """
        print("Setup: Multiple groups of adjacent messages...")
        messages = [
            UnifiedMessage(role="user", content="A"),
            UnifiedMessage(role="user", content="B"),
            UnifiedMessage(role="assistant", content="C"),
            UnifiedMessage(role="assistant", content="D"),
            UnifiedMessage(role="user", content="E")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
        assert result[0].role == "user"
        assert result[1].role == "assistant"
        assert result[2].role == "user"
    
    def test_merges_list_contents_correctly(self):
        """
        What it does: Verifies merging of list contents.
        Purpose: Ensure lists are merged correctly.
        """
        print("Setup: Two user messages with list content...")
        messages = [
            UnifiedMessage(role="user", content=[{"type": "text", "text": "Part 1"}]),
            UnifiedMessage(role="user", content=[{"type": "text", "text": "Part 2"}])
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert isinstance(result[0].content, list)
        assert len(result[0].content) == 2
    
    def test_merges_adjacent_assistant_tool_calls(self):
        """
        What it does: Verifies merging of tool_calls when merging adjacent assistant messages.
        Purpose: Ensure tool_calls from all assistant messages are preserved when merging.
        
        This is a critical test for a bug where multiple assistant messages with tool_calls
        were sent in a row, and the second tool_call was lost.
        """
        print("Setup: Two assistant messages with different tool_calls...")
        messages = [
            UnifiedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "tooluse_first",
                    "type": "function",
                    "function": {"name": "shell", "arguments": '{"command": ["ls"]}'}
                }]
            ),
            UnifiedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "tooluse_second",
                    "type": "function",
                    "function": {"name": "shell", "arguments": '{"command": ["pwd"]}'}
                }]
            )
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].role == "assistant"
        
        print("Checking that both tool_calls are preserved...")
        assert result[0].tool_calls is not None
        print(f"Comparing tool_calls count: Expected 2, Got {len(result[0].tool_calls)}")
        assert len(result[0].tool_calls) == 2
        
        tool_ids = [tc["id"] for tc in result[0].tool_calls]
        print(f"Tool IDs: {tool_ids}")
        assert "tooluse_first" in tool_ids
        assert "tooluse_second" in tool_ids
    
    def test_merges_three_adjacent_assistant_tool_calls(self):
        """
        What it does: Verifies merging of tool_calls from three assistant messages.
        Purpose: Ensure all tool_calls are preserved when merging more than two messages.
        """
        print("Setup: Three assistant messages with tool_calls...")
        messages = [
            UnifiedMessage(role="assistant", content="", tool_calls=[
                {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
            ]),
            UnifiedMessage(role="assistant", content="", tool_calls=[
                {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}
            ]),
            UnifiedMessage(role="assistant", content="", tool_calls=[
                {"id": "call_3", "type": "function", "function": {"name": "tool3", "arguments": "{}"}}
            ])
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert len(result[0].tool_calls) == 3
        
        tool_ids = [tc["id"] for tc in result[0].tool_calls]
        print(f"Comparing tool IDs: Expected ['call_1', 'call_2', 'call_3'], Got {tool_ids}")
        assert tool_ids == ["call_1", "call_2", "call_3"]
    
    def test_merges_assistant_with_and_without_tool_calls(self):
        """
        What it does: Verifies merging of assistant with and without tool_calls.
        Purpose: Ensure tool_calls are correctly initialized when merging.
        """
        print("Setup: Assistant without tool_calls + assistant with tool_calls...")
        messages = [
            UnifiedMessage(role="assistant", content="Thinking...", tool_calls=None),
            UnifiedMessage(role="assistant", content="", tool_calls=[
                {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
            ])
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0].tool_calls is not None
        print(f"Comparing tool_calls count: Expected 1, Got {len(result[0].tool_calls)}")
        assert len(result[0].tool_calls) == 1
        assert result[0].tool_calls[0]["id"] == "call_1"
    
    def test_merges_user_messages_with_tool_results(self):
        """
        What it does: Verifies merging of user messages with tool_results.
        Purpose: Ensure tool_results are preserved when merging user messages.
        """
        print("Setup: Two user messages with tool_results...")
        messages = [
            UnifiedMessage(role="user", content="", tool_results=[
                {"type": "tool_result", "tool_use_id": "call_1", "content": "Result 1"}
            ]),
            UnifiedMessage(role="user", content="", tool_results=[
                {"type": "tool_result", "tool_use_id": "call_2", "content": "Result 2"}
            ])
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0].tool_results is not None
        assert len(result[0].tool_results) == 2


# ==================================================================================================
# Tests for ensure_assistant_before_tool_results
# ==================================================================================================

class TestEnsureAssistantBeforeToolResults:
    """
    Tests for ensure_assistant_before_tool_results function.
    
    This function handles the case when clients (like Cline/Roo) send truncated
    conversations with tool_results but without the preceding assistant message
    that contains the tool_calls. Since we don't know the original tool name,
    we strip the orphaned tool_results to avoid Kiro API rejection.
    """
    
    def test_returns_empty_list_for_empty_input(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty input returns empty output.
        """
        print("Setup: Empty list...")
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results([])
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
        assert stripped is False
    
    def test_preserves_messages_without_tool_results(self):
        """
        What it does: Verifies messages without tool_results are unchanged.
        Purpose: Ensure regular messages pass through unmodified.
        """
        print("Setup: Messages without tool_results...")
        messages = [
            UnifiedMessage(role="user", content="Hello"),
            UnifiedMessage(role="assistant", content="Hi there"),
            UnifiedMessage(role="user", content="How are you?")
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
        assert result[0].content == "Hello"
        assert result[1].content == "Hi there"
        assert result[2].content == "How are you?"
        assert stripped is False
    
    def test_preserves_tool_results_with_preceding_assistant(self):
        """
        What it does: Verifies tool_results are preserved when assistant with tool_calls precedes.
        Purpose: Ensure valid tool_results are not stripped.
        """
        print("Setup: Valid conversation with assistant tool_calls followed by user tool_results...")
        messages = [
            UnifiedMessage(role="user", content="Call a tool"),
            UnifiedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"location": "Moscow"}'}
                }]
            ),
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_123",
                    "content": "Weather is sunny"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
        
        print("Checking that tool_results are preserved...")
        assert result[2].tool_results is not None
        assert len(result[2].tool_results) == 1
        assert result[2].tool_results[0]["tool_use_id"] == "call_123"
        assert stripped is False
    
    def test_strips_orphaned_tool_results_at_start(self):
        """
        What it does: Verifies orphaned tool_results at the start are stripped.
        Purpose: Ensure tool_results without preceding assistant are removed.
        
        This is the critical bug fix test - when a client sends a truncated
        conversation starting with tool_results, they should be stripped.
        """
        print("Setup: Conversation starting with orphaned tool_results...")
        messages = [
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_orphan",
                    "content": "Orphaned result"
                }]
            ),
            UnifiedMessage(role="user", content="Continue the conversation")
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 2, Got {len(result)}")
        assert len(result) == 2
        
        print("Checking that orphaned tool_results are stripped...")
        assert result[0].tool_results is None
        assert result[0].content == ""  # Content preserved
        assert result[1].content == "Continue the conversation"
        assert stripped is True
    
    def test_strips_tool_results_after_assistant_without_tool_calls(self):
        """
        What it does: Verifies tool_results are stripped when preceding assistant has no tool_calls.
        Purpose: Ensure tool_results require assistant with tool_calls, not just any assistant.
        """
        print("Setup: Assistant without tool_calls followed by user with tool_results...")
        messages = [
            UnifiedMessage(role="user", content="Hello"),
            UnifiedMessage(role="assistant", content="Let me think...", tool_calls=None),
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_123",
                    "content": "Result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that tool_results are stripped...")
        assert result[2].tool_results is None
        assert stripped is True
    
    def test_strips_tool_results_after_user_message(self):
        """
        What it does: Verifies tool_results are stripped when preceded by user message.
        Purpose: Ensure tool_results require assistant, not user.
        """
        print("Setup: User message followed by user with tool_results...")
        messages = [
            UnifiedMessage(role="user", content="First message"),
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_123",
                    "content": "Result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that tool_results are stripped...")
        assert result[1].tool_results is None
        assert stripped is True
    
    def test_preserves_content_when_stripping_tool_results(self):
        """
        What it does: Verifies message content is preserved when tool_results are stripped.
        Purpose: Ensure only tool_results are removed, not the entire message.
        """
        print("Setup: Message with both content and orphaned tool_results...")
        messages = [
            UnifiedMessage(
                role="user",
                content="Here is some context",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_123",
                    "content": "Result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that content is preserved...")
        assert result[0].content == "Here is some context"
        assert result[0].tool_results is None
        assert stripped is True
    
    def test_preserves_tool_calls_when_stripping_tool_results(self):
        """
        What it does: Verifies tool_calls are preserved when tool_results are stripped.
        Purpose: Ensure only tool_results are removed, tool_calls stay.
        """
        print("Setup: Message with tool_calls and orphaned tool_results...")
        messages = [
            UnifiedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "call_new",
                    "type": "function",
                    "function": {"name": "new_tool", "arguments": "{}"}
                }],
                tool_results=[{  # This shouldn't happen but let's test it
                    "type": "tool_result",
                    "tool_use_id": "call_old",
                    "content": "Old result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that tool_calls are preserved...")
        assert result[0].tool_calls is not None
        assert len(result[0].tool_calls) == 1
        assert result[0].tool_results is None
        assert stripped is True
    
    def test_handles_multiple_orphaned_tool_results(self):
        """
        What it does: Verifies multiple orphaned tool_results are all stripped.
        Purpose: Ensure all tool_results in the list are removed.
        """
        print("Setup: Message with multiple orphaned tool_results...")
        messages = [
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[
                    {"type": "tool_result", "tool_use_id": "call_1", "content": "Result 1"},
                    {"type": "tool_result", "tool_use_id": "call_2", "content": "Result 2"},
                    {"type": "tool_result", "tool_use_id": "call_3", "content": "Result 3"}
                ]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that all tool_results are stripped...")
        assert result[0].tool_results is None
        assert stripped is True
    
    def test_mixed_valid_and_orphaned_tool_results(self):
        """
        What it does: Verifies correct handling of mixed valid and orphaned tool_results.
        Purpose: Ensure valid tool_results are preserved while orphaned are stripped.
        """
        print("Setup: Mixed conversation with valid and orphaned tool_results...")
        messages = [
            # Orphaned tool_results at start
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_orphan",
                    "content": "Orphaned"
                }]
            ),
            # Valid assistant with tool_calls
            UnifiedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "call_valid",
                    "type": "function",
                    "function": {"name": "valid_tool", "arguments": "{}"}
                }]
            ),
            # Valid tool_results
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_valid",
                    "content": "Valid result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking orphaned tool_results are stripped...")
        assert result[0].tool_results is None
        
        print("Checking valid tool_results are preserved...")
        assert result[2].tool_results is not None
        assert result[2].tool_results[0]["tool_use_id"] == "call_valid"
        assert stripped is True  # Because orphaned ones were stripped
    
    def test_single_message_with_tool_results(self):
        """
        What it does: Verifies handling of single message with tool_results.
        Purpose: Ensure single orphaned message is handled correctly.
        """
        print("Setup: Single message with tool_results...")
        messages = [
            UnifiedMessage(
                role="user",
                content="",
                tool_results=[{
                    "type": "tool_result",
                    "tool_use_id": "call_123",
                    "content": "Result"
                }]
            )
        ]
        
        print("Action: Processing messages...")
        result, stripped = ensure_assistant_before_tool_results(messages)
        
        print(f"Result: {result}")
        print("Checking that tool_results are stripped...")
        assert len(result) == 1
        assert result[0].tool_results is None
        assert stripped is True


# ==================================================================================================
# Tests for sanitize_json_schema
# ==================================================================================================

class TestSanitizeJsonSchema:
    """
    Tests for sanitize_json_schema function.
    
    This function cleans JSON Schema from fields that Kiro API doesn't accept:
    - Empty required arrays []
    - additionalProperties
    """
    
    def test_returns_empty_dict_for_none(self):
        """
        What it does: Verifies handling of None.
        Purpose: Ensure None returns empty dict.
        """
        print("Setup: None schema...")
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(None)
        
        print(f"Comparing result: Expected {{}}, Got {result}")
        assert result == {}
    
    def test_returns_empty_dict_for_empty_dict(self):
        """
        What it does: Verifies handling of empty dict.
        Purpose: Ensure empty dict is returned as-is.
        """
        print("Setup: Empty dict...")
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema({})
        
        print(f"Comparing result: Expected {{}}, Got {result}")
        assert result == {}
    
    def test_removes_empty_required_array(self):
        """
        What it does: Verifies removal of empty required array.
        Purpose: Ensure required: [] is removed from schema.
        
        This is a critical test for a bug where tools with required: []
        caused a 400 "Improperly formed request" error from Kiro API.
        """
        print("Setup: Schema with empty required...")
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that required is removed...")
        assert "required" not in result
        assert result["type"] == "object"
        assert result["properties"] == {}
    
    def test_preserves_non_empty_required_array(self):
        """
        What it does: Verifies preservation of non-empty required array.
        Purpose: Ensure required with elements is preserved.
        """
        print("Setup: Schema with non-empty required...")
        schema = {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that required is preserved...")
        assert "required" in result
        assert result["required"] == ["location"]
    
    def test_removes_additional_properties(self):
        """
        What it does: Verifies removal of additionalProperties.
        Purpose: Ensure additionalProperties is removed from schema.
        
        Kiro API doesn't support additionalProperties in JSON Schema.
        """
        print("Setup: Schema with additionalProperties...")
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that additionalProperties is removed...")
        assert "additionalProperties" not in result
        assert result["type"] == "object"
    
    def test_removes_both_empty_required_and_additional_properties(self):
        """
        What it does: Verifies removal of both problematic fields.
        Purpose: Ensure both fields are removed simultaneously.
        """
        print("Setup: Schema with both problematic fields...")
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that both fields are removed...")
        assert "required" not in result
        assert "additionalProperties" not in result
        assert result == {"type": "object", "properties": {}}
    
    def test_recursively_sanitizes_nested_properties(self):
        """
        What it does: Verifies recursive sanitization of nested properties.
        Purpose: Ensure nested schemas are also sanitized.
        """
        print("Setup: Schema with nested properties...")
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            }
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking nested object...")
        nested = result["properties"]["nested"]
        assert "required" not in nested
        assert "additionalProperties" not in nested
    
    def test_sanitizes_items_in_lists(self):
        """
        What it does: Verifies sanitization of items in lists (anyOf, oneOf).
        Purpose: Ensure list elements are also sanitized.
        """
        print("Setup: Schema with anyOf...")
        schema = {
            "anyOf": [
                {"type": "string", "additionalProperties": False},
                {"type": "number", "required": []}
            ]
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking anyOf elements...")
        assert "additionalProperties" not in result["anyOf"][0]
        assert "required" not in result["anyOf"][1]
    
    def test_preserves_non_dict_list_items(self):
        """
        What it does: Verifies preservation of non-dict list items.
        Purpose: Ensure strings and other types in lists are preserved.
        """
        print("Setup: Schema with enum...")
        schema = {
            "type": "string",
            "enum": ["value1", "value2", "value3"]
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking enum is preserved...")
        assert result["enum"] == ["value1", "value2", "value3"]
    
    def test_complex_real_world_schema(self):
        """
        What it does: Verifies sanitization of real complex schema.
        Purpose: Ensure real schemas are handled correctly.
        """
        print("Setup: Real schema...")
        schema = {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask"},
                "options": {"type": "string", "description": "Array of options"}
            },
            "required": ["question", "options"],
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking result...")
        assert "additionalProperties" not in result
        assert result["required"] == ["question", "options"]  # Non-empty required is preserved
        assert result["properties"]["question"]["type"] == "string"


# ==================================================================================================
# Tests for extract_tool_results_from_content
# ==================================================================================================

class TestExtractToolResults:
    """Tests for extract_tool_results_from_content function."""
    
    def test_extracts_tool_results_from_list(self):
        """
        What it does: Verifies extraction of tool results from list.
        Purpose: Ensure tool_result elements are extracted.
        """
        print("Setup: List with tool_result...")
        content = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": "Result text"}
        ]
        
        print("Action: Extracting tool results...")
        result = extract_tool_results_from_content(content)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["toolUseId"] == "call_123"
        assert result[0]["status"] == "success"
    
    def test_returns_empty_for_string_content(self):
        """
        What it does: Verifies empty list return for string.
        Purpose: Ensure string doesn't contain tool results.
        """
        print("Setup: String...")
        content = "Just a string"
        
        print("Action: Extracting tool results...")
        result = extract_tool_results_from_content(content)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_returns_empty_for_list_without_tool_results(self):
        """
        What it does: Verifies empty list return without tool_result.
        Purpose: Ensure regular elements are not extracted.
        """
        print("Setup: List without tool_result...")
        content = [{"type": "text", "text": "Hello"}]
        
        print("Action: Extracting tool results...")
        result = extract_tool_results_from_content(content)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_extracts_multiple_tool_results(self):
        """
        What it does: Verifies extraction of multiple tool results.
        Purpose: Ensure all tool_result elements are extracted.
        """
        print("Setup: List with multiple tool_results...")
        content = [
            {"type": "tool_result", "tool_use_id": "call_1", "content": "Result 1"},
            {"type": "text", "text": "Some text"},
            {"type": "tool_result", "tool_use_id": "call_2", "content": "Result 2"}
        ]
        
        print("Action: Extracting tool results...")
        result = extract_tool_results_from_content(content)
        
        print(f"Result: {result}")
        assert len(result) == 2
        assert result[0]["toolUseId"] == "call_1"
        assert result[1]["toolUseId"] == "call_2"


# ==================================================================================================
# Tests for convert_tool_results_to_kiro_format
# ==================================================================================================

class TestConvertToolResultsToKiroFormat:
    """
    Tests for convert_tool_results_to_kiro_format function.
    
    This function converts unified tool results format (snake_case) to Kiro API format (camelCase).
    
    Unified format: {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    Kiro format: {"content": [{"text": "..."}], "status": "success", "toolUseId": "..."}
    
    This is a critical function for fixing the 400 "Improperly formed request" bug
    where tool_results were sent in unified format instead of Kiro format.
    """
    
    def test_converts_single_tool_result(self):
        """
        What it does: Verifies conversion of a single tool result.
        Purpose: Ensure basic conversion from unified to Kiro format works.
        """
        print("Setup: Single tool result in unified format...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": "Result text"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking structure...")
        assert len(result) == 1
        
        print("Checking toolUseId (camelCase)...")
        assert result[0]["toolUseId"] == "call_123"
        
        print("Checking status...")
        assert result[0]["status"] == "success"
        
        print("Checking content structure...")
        assert "content" in result[0]
        assert isinstance(result[0]["content"], list)
        assert len(result[0]["content"]) == 1
        assert result[0]["content"][0]["text"] == "Result text"
    
    def test_converts_multiple_tool_results(self):
        """
        What it does: Verifies conversion of multiple tool results.
        Purpose: Ensure all tool results are converted correctly.
        """
        print("Setup: Multiple tool results...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_1", "content": "Result 1"},
            {"type": "tool_result", "tool_use_id": "call_2", "content": "Result 2"},
            {"type": "tool_result", "tool_use_id": "call_3", "content": "Result 3"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print(f"Comparing count: Expected 3, Got {len(result)}")
        assert len(result) == 3
        
        print("Checking all toolUseIds...")
        assert result[0]["toolUseId"] == "call_1"
        assert result[1]["toolUseId"] == "call_2"
        assert result[2]["toolUseId"] == "call_3"
        
        print("Checking all contents...")
        assert result[0]["content"][0]["text"] == "Result 1"
        assert result[1]["content"][0]["text"] == "Result 2"
        assert result[2]["content"][0]["text"] == "Result 3"
    
    def test_returns_empty_list_for_empty_input(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty input returns empty output.
        """
        print("Setup: Empty list...")
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format([])
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_replaces_empty_content_with_placeholder(self):
        """
        What it does: Verifies empty content is replaced with placeholder.
        Purpose: Ensure Kiro API receives non-empty content (required by API).
        """
        print("Setup: Tool result with empty content...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": ""}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that empty content is replaced with placeholder...")
        assert result[0]["content"][0]["text"] == "(empty result)"
    
    def test_replaces_none_content_with_placeholder(self):
        """
        What it does: Verifies None content is replaced with placeholder.
        Purpose: Ensure Kiro API receives non-empty content when content is None.
        """
        print("Setup: Tool result with None content...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": None}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that None content is replaced with placeholder...")
        assert result[0]["content"][0]["text"] == "(empty result)"
    
    def test_handles_missing_content_key(self):
        """
        What it does: Verifies handling of missing content key.
        Purpose: Ensure function doesn't crash when content key is missing.
        """
        print("Setup: Tool result without content key...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that missing content is replaced with placeholder...")
        assert result[0]["content"][0]["text"] == "(empty result)"
    
    def test_handles_missing_tool_use_id(self):
        """
        What it does: Verifies handling of missing tool_use_id.
        Purpose: Ensure function returns empty string for missing tool_use_id.
        """
        print("Setup: Tool result without tool_use_id...")
        tool_results = [
            {"type": "tool_result", "content": "Result text"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that missing tool_use_id becomes empty string...")
        assert result[0]["toolUseId"] == ""
        assert result[0]["content"][0]["text"] == "Result text"
    
    def test_extracts_text_from_list_content(self):
        """
        What it does: Verifies extraction of text from list content.
        Purpose: Ensure multimodal content format is handled correctly.
        """
        print("Setup: Tool result with list content...")
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": "call_123",
                "content": [
                    {"type": "text", "text": "Part 1"},
                    {"type": "text", "text": " Part 2"}
                ]
            }
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that list content is extracted correctly...")
        assert result[0]["content"][0]["text"] == "Part 1 Part 2"
    
    def test_preserves_long_content(self):
        """
        What it does: Verifies long content is preserved.
        Purpose: Ensure large tool results are not truncated.
        """
        print("Setup: Tool result with long content...")
        long_content = "A" * 10000
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": long_content}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result content length: {len(result[0]['content'][0]['text'])}")
        print("Checking that long content is preserved...")
        assert result[0]["content"][0]["text"] == long_content
        assert len(result[0]["content"][0]["text"]) == 10000
    
    def test_all_results_have_success_status(self):
        """
        What it does: Verifies all results have status="success".
        Purpose: Ensure Kiro API receives correct status field.
        """
        print("Setup: Multiple tool results...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_1", "content": "Result 1"},
            {"type": "tool_result", "tool_use_id": "call_2", "content": "Result 2"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print("Checking all statuses...")
        for i, r in enumerate(result):
            print(f"Result {i}: status = {r['status']}")
            assert r["status"] == "success"
    
    def test_handles_unicode_content(self):
        """
        What it does: Verifies Unicode content is preserved.
        Purpose: Ensure non-ASCII characters are handled correctly.
        """
        print("Setup: Tool result with Unicode content...")
        tool_results = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": "Привет мир! 你好世界! 🎉"}
        ]
        
        print("Action: Converting to Kiro format...")
        result = convert_tool_results_to_kiro_format(tool_results)
        
        print(f"Result: {result}")
        print("Checking that Unicode content is preserved...")
        assert result[0]["content"][0]["text"] == "Привет мир! 你好世界! 🎉"


# ==================================================================================================
# Tests for extract_tool_uses_from_message
# ==================================================================================================

class TestExtractToolUses:
    """Tests for extract_tool_uses_from_message function."""
    
    def test_extracts_from_tool_calls_field(self):
        """
        What it does: Verifies extraction from tool_calls field.
        Purpose: Ensure OpenAI tool_calls format is handled.
        """
        print("Setup: tool_calls list...")
        tool_calls = [{
            "id": "call_123",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "Moscow"}'
            }
        }]
        
        print("Action: Extracting tool uses...")
        result = extract_tool_uses_from_message(content="", tool_calls=tool_calls)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["toolUseId"] == "call_123"
    
    def test_extracts_from_content_list(self):
        """
        What it does: Verifies extraction from content list.
        Purpose: Ensure tool_use in content is handled (Anthropic format).
        """
        print("Setup: Content with tool_use...")
        content = [{
            "type": "tool_use",
            "id": "call_456",
            "name": "search",
            "input": {"query": "test"}
        }]
        
        print("Action: Extracting tool uses...")
        result = extract_tool_uses_from_message(content=content, tool_calls=None)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["toolUseId"] == "call_456"
    
    def test_returns_empty_for_no_tool_uses(self):
        """
        What it does: Verifies empty list return without tool uses.
        Purpose: Ensure regular message doesn't contain tool uses.
        """
        print("Setup: Regular content...")
        
        print("Action: Extracting tool uses...")
        result = extract_tool_uses_from_message(content="Hello", tool_calls=None)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_extracts_from_both_sources(self):
        """
        What it does: Verifies extraction from both tool_calls and content.
        Purpose: Ensure both sources are combined.
        """
        print("Setup: Both tool_calls and content with tool_use...")
        tool_calls = [{
            "id": "call_1",
            "function": {"name": "tool1", "arguments": "{}"}
        }]
        content = [{
            "type": "tool_use",
            "id": "call_2",
            "name": "tool2",
            "input": {}
        }]
        
        print("Action: Extracting tool uses...")
        result = extract_tool_uses_from_message(content=content, tool_calls=tool_calls)
        
        print(f"Result: {result}")
        assert len(result) == 2


# ==================================================================================================
# Tests for process_tools_with_long_descriptions
# ==================================================================================================

class TestProcessToolsWithLongDescriptions:
    """Tests for process_tools_with_long_descriptions function using UnifiedTool."""
    
    def test_returns_none_and_empty_string_for_none_tools(self):
        """
        What it does: Verifies handling of None instead of tools list.
        Purpose: Ensure None returns (None, "").
        """
        print("Setup: None instead of tools...")
        
        print("Action: Processing tools...")
        processed, doc = process_tools_with_long_descriptions(None)
        
        print(f"Comparing result: Expected (None, ''), Got ({processed}, '{doc}')")
        assert processed is None
        assert doc == ""
    
    def test_returns_none_and_empty_string_for_empty_list(self):
        """
        What it does: Verifies handling of empty tools list.
        Purpose: Ensure empty list returns (None, "").
        """
        print("Setup: Empty tools list...")
        
        print("Action: Processing tools...")
        processed, doc = process_tools_with_long_descriptions([])
        
        print(f"Comparing result: Expected (None, ''), Got ({processed}, '{doc}')")
        assert processed is None
        assert doc == ""
    
    def test_short_description_unchanged(self):
        """
        What it does: Verifies short descriptions are unchanged.
        Purpose: Ensure tools with short descriptions remain as-is.
        """
        print("Setup: Tool with short description...")
        tools = [UnifiedTool(
            name="get_weather",
            description="Get weather for a location",
            input_schema={"type": "object", "properties": {}}
        )]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Comparing description: Expected 'Get weather for a location', Got '{processed[0].description}'")
        assert len(processed) == 1
        assert processed[0].description == "Get weather for a location"
        assert doc == ""
    
    def test_long_description_moved_to_system_prompt(self):
        """
        What it does: Verifies moving long description to system prompt.
        Purpose: Ensure long descriptions are moved correctly.
        """
        print("Setup: Tool with very long description...")
        long_description = "A" * 15000  # 15000 chars - exceeds limit
        tools = [UnifiedTool(
            name="bash",
            description=long_description,
            input_schema={"type": "object", "properties": {"command": {"type": "string"}}}
        )]
        
        print("Action: Processing tools with limit 10000...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking reference in description...")
        assert len(processed) == 1
        assert "[Full documentation in system prompt under '## Tool: bash']" in processed[0].description
        
        print("Checking documentation in system prompt...")
        assert "## Tool: bash" in doc
        assert long_description in doc
        assert "# Tool Documentation" in doc
    
    def test_mixed_short_and_long_descriptions(self):
        """
        What it does: Verifies handling of mixed tools list.
        Purpose: Ensure short ones stay, long ones are moved.
        """
        print("Setup: Two tools - short and long...")
        short_desc = "Short description"
        long_desc = "B" * 15000
        tools = [
            UnifiedTool(name="short_tool", description=short_desc, input_schema={}),
            UnifiedTool(name="long_tool", description=long_desc, input_schema={})
        ]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking tools count: Expected 2, Got {len(processed)}")
        assert len(processed) == 2
        
        print("Checking short tool...")
        assert processed[0].description == short_desc
        
        print("Checking long tool...")
        assert "[Full documentation in system prompt" in processed[1].description
        assert "## Tool: long_tool" in doc
        assert long_desc in doc
    
    def test_disabled_when_limit_is_zero(self):
        """
        What it does: Verifies function is disabled when limit is 0.
        Purpose: Ensure tools are unchanged when TOOL_DESCRIPTION_MAX_LENGTH=0.
        """
        print("Setup: Tool with long description and limit 0...")
        long_desc = "D" * 15000
        tools = [UnifiedTool(name="test_tool", description=long_desc, input_schema={})]
        
        print("Action: Processing tools with limit 0...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 0):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking that description is unchanged...")
        assert processed[0].description == long_desc
        assert doc == ""
    
    def test_multiple_long_descriptions_all_moved(self):
        """
        What it does: Verifies moving of multiple long descriptions.
        Purpose: Ensure all long descriptions are moved.
        """
        print("Setup: Three tools with long descriptions...")
        tools = [
            UnifiedTool(name="tool1", description="F" * 15000, input_schema={}),
            UnifiedTool(name="tool2", description="G" * 15000, input_schema={}),
            UnifiedTool(name="tool3", description="H" * 15000, input_schema={})
        ]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking all three tools...")
        assert len(processed) == 3
        for tool in processed:
            assert "[Full documentation in system prompt" in tool.description
        
        print("Checking documentation contains all three sections...")
        assert "## Tool: tool1" in doc
        assert "## Tool: tool2" in doc
        assert "## Tool: tool3" in doc
    
    def test_empty_description_unchanged(self):
        """
        What it does: Verifies handling of empty description.
        Purpose: Ensure empty description doesn't cause errors.
        """
        print("Setup: Tool with empty description...")
        tools = [UnifiedTool(name="empty_desc_tool", description="", input_schema={})]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking that empty description remains empty...")
        assert processed[0].description == ""
        assert doc == ""
    
    def test_none_description_unchanged(self):
        """
        What it does: Verifies handling of None description.
        Purpose: Ensure None description doesn't cause errors.
        """
        print("Setup: Tool with None description...")
        tools = [UnifiedTool(name="none_desc_tool", description=None, input_schema={})]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking that None description is handled correctly...")
        # None should remain None or become empty string
        assert processed[0].description is None or processed[0].description == ""
        assert doc == ""
    
    def test_preserves_tool_input_schema(self):
        """
        What it does: Verifies input_schema preservation when moving description.
        Purpose: Ensure input_schema is not lost.
        """
        print("Setup: Tool with input_schema and long description...")
        input_schema = {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
        tools = [UnifiedTool(
            name="weather",
            description="C" * 15000,
            input_schema=input_schema
        )]
        
        print("Action: Processing tools...")
        with patch('kiro.converters_core.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print("Checking input_schema preservation...")
        assert processed[0].input_schema == input_schema


# ==================================================================================================
# Tests for convert_tools_to_kiro_format
# ==================================================================================================

class TestConvertToolsToKiroFormat:
    """Tests for convert_tools_to_kiro_format function."""
    
    def test_returns_empty_list_for_none(self):
        """
        What it does: Verifies handling of None.
        Purpose: Ensure None returns empty list.
        """
        print("Setup: None tools...")
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format(None)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_returns_empty_list_for_empty_list(self):
        """
        What it does: Verifies handling of empty list.
        Purpose: Ensure empty list returns empty list.
        """
        print("Setup: Empty tools list...")
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format([])
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_converts_tool_to_kiro_format(self):
        """
        What it does: Verifies conversion of tool to Kiro format.
        Purpose: Ensure toolSpecification structure is correct.
        """
        print("Setup: Tool...")
        tools = [UnifiedTool(
            name="get_weather",
            description="Get weather for a location",
            input_schema={"type": "object", "properties": {"location": {"type": "string"}}}
        )]
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format(tools)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "toolSpecification" in result[0]
        spec = result[0]["toolSpecification"]
        assert spec["name"] == "get_weather"
        assert spec["description"] == "Get weather for a location"
        assert "inputSchema" in spec
        assert "json" in spec["inputSchema"]
    
    def test_replaces_empty_description_with_placeholder(self):
        """
        What it does: Verifies replacement of empty description.
        Purpose: Ensure empty description is replaced with "Tool: {name}".
        """
        print("Setup: Tool with empty description...")
        tools = [UnifiedTool(name="focus_chain", description="", input_schema={})]
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format(tools)
        
        print(f"Result: {result}")
        spec = result[0]["toolSpecification"]
        assert spec["description"] == "Tool: focus_chain"
    
    def test_replaces_none_description_with_placeholder(self):
        """
        What it does: Verifies replacement of None description.
        Purpose: Ensure None description is replaced with "Tool: {name}".
        """
        print("Setup: Tool with None description...")
        tools = [UnifiedTool(name="test_tool", description=None, input_schema={})]
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format(tools)
        
        print(f"Result: {result}")
        spec = result[0]["toolSpecification"]
        assert spec["description"] == "Tool: test_tool"
    
    def test_sanitizes_input_schema(self):
        """
        What it does: Verifies sanitization of input schema.
        Purpose: Ensure problematic fields are removed from schema.
        """
        print("Setup: Tool with problematic schema...")
        tools = [UnifiedTool(
            name="test_tool",
            description="Test",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        )]
        
        print("Action: Converting tools...")
        result = convert_tools_to_kiro_format(tools)
        
        print(f"Result: {result}")
        schema = result[0]["toolSpecification"]["inputSchema"]["json"]
        assert "required" not in schema
        assert "additionalProperties" not in schema


# ==================================================================================================
# Tests for inject_thinking_tags
# ==================================================================================================

class TestInjectThinkingTags:
    """
    Tests for inject_thinking_tags function.
    
    This function injects thinking mode tags into content when FAKE_REASONING_ENABLED is True.
    """
    
    def test_returns_original_content_when_disabled(self):
        """
        What it does: Verifies that content is returned unchanged when fake reasoning is disabled.
        Purpose: Ensure no modification occurs when FAKE_REASONING_ENABLED=False.
        """
        print("Setup: Content with fake reasoning disabled...")
        content = "Hello, world!"
        
        print("Action: Inject thinking tags with FAKE_REASONING_ENABLED=False...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', False):
            result = inject_thinking_tags(content)
        
        print(f"Comparing result: Expected 'Hello, world!', Got '{result}'")
        assert result == "Hello, world!"
    
    def test_injects_tags_when_enabled(self):
        """
        What it does: Verifies that thinking tags are injected when enabled.
        Purpose: Ensure tags are prepended to content when FAKE_REASONING_ENABLED=True.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "What is 2+2?"
        
        print("Action: Inject thinking tags with FAKE_REASONING_ENABLED=True...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print(f"Result: {result[:200]}...")
        print("Checking that thinking_mode tag is present...")
        assert "<thinking_mode>enabled</thinking_mode>" in result
        
        print("Checking that max_thinking_length tag is present...")
        assert "<max_thinking_length>4000</max_thinking_length>" in result
        
        print("Checking that original content is preserved at the end...")
        assert result.endswith("What is 2+2?")
    
    def test_injects_thinking_instruction_tag(self):
        """
        What it does: Verifies that thinking_instruction tag is injected.
        Purpose: Ensure the quality improvement prompt is included.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Analyze this code"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 8000):
                result = inject_thinking_tags(content)
        
        print(f"Result length: {len(result)} chars")
        print("Checking that thinking_instruction tag is present...")
        assert "<thinking_instruction>" in result
        assert "</thinking_instruction>" in result
    
    def test_thinking_instruction_contains_english_directive(self):
        """
        What it does: Verifies that thinking instruction includes English language directive.
        Purpose: Ensure model is instructed to think in English for better reasoning quality.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for English directive...")
        assert "Think in English" in result
    
    def test_uses_configured_max_tokens(self):
        """
        What it does: Verifies that FAKE_REASONING_MAX_TOKENS config value is used.
        Purpose: Ensure the configured max tokens value is injected into the tag.
        """
        print("Setup: Content with custom max tokens...")
        content = "Test"
        
        print("Action: Inject thinking tags with FAKE_REASONING_MAX_TOKENS=16000...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 16000):
                result = inject_thinking_tags(content)
        
        print(f"Result: {result[:300]}...")
        print("Checking that max_thinking_length uses configured value...")
        assert "<max_thinking_length>16000</max_thinking_length>" in result
    
    def test_preserves_empty_content(self):
        """
        What it does: Verifies that empty content is handled correctly.
        Purpose: Ensure empty string doesn't cause issues.
        """
        print("Setup: Empty content with fake reasoning enabled...")
        content = ""
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print(f"Result length: {len(result)} chars")
        print("Checking that tags are present even with empty content...")
        assert "<thinking_mode>enabled</thinking_mode>" in result
        assert "<thinking_instruction>" in result
    
    def test_preserves_multiline_content(self):
        """
        What it does: Verifies that multiline content is preserved correctly.
        Purpose: Ensure newlines in original content are not corrupted.
        """
        print("Setup: Multiline content...")
        content = "Line 1\nLine 2\nLine 3"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking that multiline content is preserved...")
        assert "Line 1\nLine 2\nLine 3" in result
    
    def test_preserves_special_characters(self):
        """
        What it does: Verifies that special characters in content are preserved.
        Purpose: Ensure XML-like content in user message doesn't break injection.
        """
        print("Setup: Content with special characters...")
        content = "Check this <code>example</code> and {json: 'value'}"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking that special characters are preserved...")
        assert "<code>example</code>" in result
        assert "{json: 'value'}" in result
    
    def test_thinking_instruction_contains_systematic_approach(self):
        """
        What it does: Verifies that thinking instruction includes systematic approach guidance.
        Purpose: Ensure model is instructed to think systematically.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for systematic approach keywords...")
        assert "thorough" in result.lower() or "systematic" in result.lower()
    
    def test_thinking_instruction_contains_understanding_step(self):
        """
        What it does: Verifies that thinking instruction includes understanding step.
        Purpose: Ensure model is instructed to understand the problem first.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for understanding step...")
        assert "understand" in result.lower()
    
    def test_thinking_instruction_contains_verification_step(self):
        """
        What it does: Verifies that thinking instruction includes verification step.
        Purpose: Ensure model is instructed to verify reasoning before concluding.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for verification step...")
        assert "verify" in result.lower()
    
    def test_thinking_instruction_contains_quality_emphasis(self):
        """
        What it does: Verifies that thinking instruction emphasizes quality over speed.
        Purpose: Ensure model is instructed to prioritize quality of thought.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for quality emphasis...")
        assert "quality" in result.lower()
    
    def test_tag_order_is_correct(self):
        """
        What it does: Verifies that tags are in the correct order.
        Purpose: Ensure thinking_mode comes first, then max_thinking_length, then instruction, then content.
        """
        print("Setup: Content...")
        content = "USER_CONTENT_HERE"
        
        print("Action: Inject thinking tags...")
        with patch('kiro.converters_core.FAKE_REASONING_ENABLED', True):
            with patch('kiro.converters_core.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking tag order...")
        thinking_mode_pos = result.find("<thinking_mode>")
        max_length_pos = result.find("<max_thinking_length>")
        instruction_pos = result.find("<thinking_instruction>")
        content_pos = result.find("USER_CONTENT_HERE")
        
        print(f"Positions: thinking_mode={thinking_mode_pos}, max_length={max_length_pos}, instruction={instruction_pos}, content={content_pos}")
        
        assert thinking_mode_pos < max_length_pos, "thinking_mode should come before max_thinking_length"
        assert max_length_pos < instruction_pos, "max_thinking_length should come before thinking_instruction"
        assert instruction_pos < content_pos, "thinking_instruction should come before user content"


# ==================================================================================================
# Tests for build_kiro_history
# ==================================================================================================

class TestBuildKiroHistory:
    """Tests for build_kiro_history function using UnifiedMessage."""
    
    def test_builds_user_message(self):
        """
        What it does: Verifies building of user message.
        Purpose: Ensure user message is converted to userInputMessage.
        """
        print("Setup: User message...")
        messages = [UnifiedMessage(role="user", content="Hello")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "userInputMessage" in result[0]
        assert result[0]["userInputMessage"]["content"] == "Hello"
        assert result[0]["userInputMessage"]["modelId"] == "claude-sonnet-4"
    
    def test_builds_assistant_message(self):
        """
        What it does: Verifies building of assistant message.
        Purpose: Ensure assistant message is converted to assistantResponseMessage.
        """
        print("Setup: Assistant message...")
        messages = [UnifiedMessage(role="assistant", content="Hi there")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "assistantResponseMessage" in result[0]
        assert result[0]["assistantResponseMessage"]["content"] == "Hi there"
    
    def test_ignores_system_messages(self):
        """
        What it does: Verifies ignoring of system messages.
        Purpose: Ensure system messages are not added to history.
        """
        print("Setup: System message...")
        messages = [UnifiedMessage(role="system", content="You are helpful")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Comparing length: Expected 0, Got {len(result)}")
        assert len(result) == 0
    
    def test_builds_conversation_history(self):
        """
        What it does: Verifies building of full conversation history.
        Purpose: Ensure user/assistant alternation is preserved.
        """
        print("Setup: Full conversation history...")
        messages = [
            UnifiedMessage(role="user", content="Hello"),
            UnifiedMessage(role="assistant", content="Hi"),
            UnifiedMessage(role="user", content="How are you?")
        ]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 3
        assert "userInputMessage" in result[0]
        assert "assistantResponseMessage" in result[1]
        assert "userInputMessage" in result[2]
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list returns empty history.
        """
        print("Setup: Empty list...")
        
        print("Action: Building history...")
        result = build_kiro_history([], "claude-sonnet-4")
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_builds_user_message_with_tool_results(self):
        """
        What it does: Verifies building of user message with tool_results.
        Purpose: Ensure tool_results are included in userInputMessageContext.
        """
        print("Setup: User message with tool_results...")
        messages = [
            UnifiedMessage(
                role="user",
                content="Here are the results",
                tool_results=[
                    {"type": "tool_result", "tool_use_id": "call_123", "content": "Result text"}
                ]
            )
        ]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "userInputMessage" in result[0]
        user_msg = result[0]["userInputMessage"]
        assert "userInputMessageContext" in user_msg
        assert "toolResults" in user_msg["userInputMessageContext"]
    
    def test_builds_assistant_message_with_tool_calls(self):
        """
        What it does: Verifies building of assistant message with tool_calls.
        Purpose: Ensure tool_calls are converted to toolUses.
        """
        print("Setup: Assistant message with tool_calls...")
        messages = [
            UnifiedMessage(
                role="assistant",
                content="I'll call a tool",
                tool_calls=[{
                    "id": "call_123",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Moscow"}'
                    }
                }]
            )
        ]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "assistantResponseMessage" in result[0]
        assistant_msg = result[0]["assistantResponseMessage"]
        assert "toolUses" in assistant_msg