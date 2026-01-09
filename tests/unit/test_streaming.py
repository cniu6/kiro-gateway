
# -*- coding: utf-8 -*-

"""
Unit tests for streaming module.
Tests logic for adding index to tool_calls and protection from None values.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from kiro.streaming_openai import (
    stream_kiro_to_openai,
    collect_stream_response
)


@pytest.fixture
def mock_model_cache():
    """Mock for ModelInfoCache."""
    cache = MagicMock()
    cache.get_max_input_tokens.return_value = 200000
    return cache


@pytest.fixture
def mock_auth_manager():
    """Mock for KiroAuthManager."""
    manager = MagicMock()
    return manager


@pytest.fixture
def mock_http_client():
    """Mock for httpx.AsyncClient."""
    client = AsyncMock()
    return client


class TestStreamingToolCallsIndex:
    """Tests for adding index to tool_calls in streaming responses."""
    
    @pytest.mark.asyncio
    async def test_tool_calls_have_index_field(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that tool_calls in streaming response contain index field.
        Goal: Ensure OpenAI API spec is followed for streaming tool calls.
        """
        print("Setup: Mock tool calls without index...")
        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "Moscow"}'
                }
            }
        ]
        
        print("Setup: Mock parser...")
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        print("Setup: Mock response...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting streaming chunks...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model", 
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        print(f"Received chunks: {len(chunks)}")
        
        # Look for chunk with tool_calls
        tool_calls_found = False
        for chunk in chunks:
            if isinstance(chunk, str) and "tool_calls" in chunk:
                if chunk.startswith("data: "):
                    json_str = chunk[6:].strip()
                    if json_str != "[DONE]":
                        data = json.loads(json_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "tool_calls" in delta:
                                print(f"Tool calls in delta: {delta['tool_calls']}")
                                for tc in delta["tool_calls"]:
                                    print(f"Checking index in tool call: {tc}")
                                    assert "index" in tc, "Tool call must contain index field"
                                    tool_calls_found = True
        
        assert tool_calls_found, "Tool calls chunk not found"
    
    @pytest.mark.asyncio
    async def test_multiple_tool_calls_have_sequential_indices(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that multiple tool_calls have sequential indices.
        Goal: Ensure indices start from 0 and go sequentially.
        """
        print("Setup: Multiple tool calls...")
        tool_calls = [
            {"id": "call_1", "type": "function", "function": {"name": "func1", "arguments": "{}"}},
            {"id": "call_2", "type": "function", "function": {"name": "func2", "arguments": "{}"}},
            {"id": "call_3", "type": "function", "function": {"name": "func3", "arguments": "{}"}}
        ]
        
        print("Setup: Mock parser...")
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        print("Setup: Mock response...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting streaming chunks...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        # Look for chunk with tool_calls
        for chunk in chunks:
            if isinstance(chunk, str) and "tool_calls" in chunk:
                if chunk.startswith("data: "):
                    json_str = chunk[6:].strip()
                    if json_str != "[DONE]":
                        data = json.loads(json_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "tool_calls" in delta:
                                indices = [tc["index"] for tc in delta["tool_calls"]]
                                print(f"Indices: {indices}")
                                assert indices == [0, 1, 2], f"Indices should be [0, 1, 2], got {indices}"


class TestStreamingToolCallsNoneProtection:
    """Tests for protection from None values in tool_calls."""
    
    @pytest.mark.asyncio
    async def test_handles_none_function_name(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies handling of None in function.name.
        Goal: Ensure None is replaced with empty string.
        """
        print("Setup: Tool call with None name...")
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": None,
                    "arguments": '{"a": 1}'
                }
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting streaming chunks...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        # Verify no exceptions and chunks collected
        print(f"Received chunks: {len(chunks)}")
        assert len(chunks) > 0
        
        # Verify name replaced with empty string
        for chunk in chunks:
            if isinstance(chunk, str) and "tool_calls" in chunk:
                if chunk.startswith("data: "):
                    json_str = chunk[6:].strip()
                    if json_str != "[DONE]":
                        data = json.loads(json_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    assert tc["function"]["name"] == "", "None name should be replaced with empty string"
    
    @pytest.mark.asyncio
    async def test_handles_none_function_arguments(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies handling of None in function.arguments.
        Goal: Ensure None is replaced with "{}".
        """
        print("Setup: Tool call with None arguments...")
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_func",
                    "arguments": None
                }
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting streaming chunks...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        print(f"Received chunks: {len(chunks)}")
        assert len(chunks) > 0
        
        # Verify arguments replaced with "{}"
        for chunk in chunks:
            if isinstance(chunk, str) and "tool_calls" in chunk:
                if chunk.startswith("data: "):
                    json_str = chunk[6:].strip()
                    if json_str != "[DONE]":
                        data = json.loads(json_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    # None should be replaced with "{}" or empty string
                                    assert tc["function"]["arguments"] is not None
    
    @pytest.mark.asyncio
    async def test_handles_none_function_object(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies handling of None instead of function object.
        Goal: Ensure None function is handled without errors.
        """
        print("Setup: Tool call with None function...")
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": None
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting streaming chunks...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        print(f"Received chunks: {len(chunks)}")
        assert len(chunks) > 0


class TestCollectStreamResponseToolCalls:
    """Tests for collect_stream_response with tool_calls."""
    
    @pytest.mark.asyncio
    async def test_collected_tool_calls_have_no_index(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that collected tool_calls don't contain index field.
        Goal: Ensure index is removed for non-streaming response.
        """
        print("Setup: Tool calls...")
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "func1", "arguments": '{"a": 1}'}
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"Hello"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting full response...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                result = await collect_stream_response(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                )
        
        print(f"Result: {result}")
        
        if "choices" in result and result["choices"]:
            message = result["choices"][0].get("message", {})
            if "tool_calls" in message:
                for tc in message["tool_calls"]:
                    print(f"Tool call: {tc}")
                    assert "index" not in tc, "Non-streaming tool_calls should not contain index"
    
    @pytest.mark.asyncio
    async def test_collected_tool_calls_have_required_fields(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that collected tool_calls contain all required fields.
        Goal: Ensure id, type, function are present.
        """
        print("Setup: Tool calls...")
        tool_calls = [
            {
                "id": "call_abc",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"city": "Moscow"}'}
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":""}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting full response...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                result = await collect_stream_response(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                )
        
        print(f"Result: {result}")
        
        if "choices" in result and result["choices"]:
            message = result["choices"][0].get("message", {})
            if "tool_calls" in message:
                for tc in message["tool_calls"]:
                    print(f"Checking tool call: {tc}")
                    assert "id" in tc, "Tool call must contain id"
                    assert "type" in tc, "Tool call must contain type"
                    assert "function" in tc, "Tool call must contain function"
                    assert "name" in tc["function"], "Function must contain name"
                    assert "arguments" in tc["function"], "Function must contain arguments"
    
    @pytest.mark.asyncio
    async def test_handles_none_in_collected_tool_calls(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies handling of None values in collected tool_calls.
        Goal: Ensure None is replaced with default values.
        """
        print("Setup: Tool calls with None values...")
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": None
            }
        ]
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = []
        mock_parser.get_tool_calls.return_value = tool_calls
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":""}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        print("Action: Collecting full response...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                result = await collect_stream_response(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                )
        
        print(f"Result: {result}")
        
        # Verify no exceptions
        assert "choices" in result


class TestStreamingErrorHandling:
    """Tests for error handling in streaming module."""
    
    @pytest.mark.asyncio
    async def test_generator_exit_handled_gracefully(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that GeneratorExit is handled without logging as error.
        Goal: Ensure client disconnect doesn't cause ERROR in logs.
        """
        print("Setup: Mock response that will raise GeneratorExit...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        # Create generator that will raise GeneratorExit
        async def mock_aiter_bytes_with_generator_exit():
            yield b'{"content":"Hello"}'
            # Simulate client disconnect
            raise GeneratorExit()
        
        mock_response.aiter_bytes = mock_aiter_bytes_with_generator_exit
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming with GeneratorExit...")
        chunks_received = []
        generator_exit_caught = False
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                try:
                    async for chunk in stream_kiro_to_openai(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager
                    ):
                        chunks_received.append(chunk)
                except GeneratorExit:
                    generator_exit_caught = True
                    print("GeneratorExit was caught (expected)")
        
        print(f"Received chunks before GeneratorExit: {len(chunks_received)}")
        print(f"GeneratorExit caught: {generator_exit_caught}")
        
        # Verify response was closed
        print("Check: response.aclose() should be called...")
        mock_response.aclose.assert_called()
        print("✓ response.aclose() was called")
    
    @pytest.mark.asyncio
    async def test_exception_with_empty_message_logged_with_type(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that exception with empty message is logged with type.
        Goal: Ensure exception type is visible in logs even if str(e) is empty.
        """
        print("Setup: Mock response that will raise exception with empty message...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        # Create custom exception with empty message
        class EmptyMessageError(Exception):
            def __str__(self):
                return ""
        
        async def mock_aiter_bytes_with_empty_error():
            yield b'{"content":"Hello"}'
            raise EmptyMessageError()
        
        mock_response.aiter_bytes = mock_aiter_bytes_with_empty_error
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming with EmptyMessageError...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                with patch('kiro.streaming_openai.logger') as mock_logger:
                    exception_raised = False
                    try:
                        async for chunk in stream_kiro_to_openai(
                            mock_http_client, mock_response, "test-model",
                            mock_model_cache, mock_auth_manager
                        ):
                            pass
                    except EmptyMessageError:
                        exception_raised = True
                        print("EmptyMessageError was caught (expected)")
                    
                    print("Check: logger.error should be called with exception type...")
                    # Verify logger.error was called
                    error_calls = [call for call in mock_logger.error.call_args_list]
                    print(f"logger.error calls: {error_calls}")
                    
                    # Should have call with exception type
                    assert exception_raised, "Exception should be propagated"
                    assert mock_logger.error.called, "logger.error should be called"
                    
                    # Verify exception type is in message
                    error_message = str(mock_logger.error.call_args_list[0])
                    print(f"Error message: {error_message}")
                    assert "EmptyMessageError" in error_message, "Exception type should be in log"
                    print("✓ Exception type is present in log")
    
    @pytest.mark.asyncio
    async def test_exception_propagated_to_caller(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that exceptions are propagated up.
        Goal: Ensure errors are not "swallowed" inside generator.
        """
        print("Setup: Mock response that will raise RuntimeError...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes_with_error():
            yield b'{"content":"Hello"}'
            raise RuntimeError("Test error for propagation")
        
        mock_response.aiter_bytes = mock_aiter_bytes_with_error
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming with RuntimeError...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                with pytest.raises(RuntimeError) as exc_info:
                    async for chunk in stream_kiro_to_openai(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager
                    ):
                        pass
        
        print(f"Caught exception: {exc_info.value}")
        assert "Test error for propagation" in str(exc_info.value)
        print("✓ Exception was propagated up with correct message")
    
    @pytest.mark.asyncio
    async def test_response_closed_on_error(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that response is closed even on error.
        Goal: Ensure resources are released in finally block.
        """
        print("Setup: Mock response that will raise ValueError...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes_with_value_error():
            yield b'{"content":"Hello"}'
            raise ValueError("Test value error")
        
        mock_response.aiter_bytes = mock_aiter_bytes_with_value_error
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming with ValueError...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                try:
                    async for chunk in stream_kiro_to_openai(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager
                    ):
                        pass
                except ValueError:
                    print("ValueError caught (expected)")
        
        print("Check: response.aclose() should be called...")
        mock_response.aclose.assert_called()
        print("✓ response.aclose() was called even on error")
    
    @pytest.mark.asyncio
    async def test_response_closed_on_success(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that response is closed on successful completion.
        Goal: Ensure resources are released in finally block.
        """
        print("Setup: Mock response for successful streaming...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes_success():
            yield b'{"content":"Hello World"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes_success
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello World"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running successful streaming...")
        chunks = []
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                async for chunk in stream_kiro_to_openai(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager
                ):
                    chunks.append(chunk)
        
        print(f"Received chunks: {len(chunks)}")
        print("Check: response.aclose() should be called...")
        mock_response.aclose.assert_called()
        print("✓ response.aclose() was called on successful completion")
    
    @pytest.mark.asyncio
    async def test_aclose_error_does_not_mask_original_error(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that error in aclose() doesn't mask original error.
        Goal: Ensure original exception is propagated even if aclose() fails.
        """
        print("Setup: Mock response with error in aclose()...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock(side_effect=ConnectionError("Connection lost"))
        
        async def mock_aiter_bytes_with_error():
            yield b'{"content":"Hello"}'
            raise RuntimeError("Original error")
        
        mock_response.aiter_bytes = mock_aiter_bytes_with_error
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming with error and error in aclose()...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                with pytest.raises(RuntimeError) as exc_info:
                    async for chunk in stream_kiro_to_openai(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager
                    ):
                        pass
        
        print(f"Caught exception: {exc_info.value}")
        # Should be original error, not ConnectionError from aclose()
        assert "Original error" in str(exc_info.value)
        print("✓ Original error was not masked by error in aclose()")


class TestFirstTokenTimeoutError:
    """Tests for FirstTokenTimeoutError and first token timeout logging."""
    
    @pytest.mark.asyncio
    async def test_first_token_timeout_not_caught_by_general_handler(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that FirstTokenTimeoutError is propagated for retry.
        Goal: Ensure first token timeout is not handled as regular error.
        """
        import asyncio
        from kiro.streaming_openai import FirstTokenTimeoutError, stream_kiro_to_openai_internal
        
        print("Setup: Mock response with timeout...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        # Create generator that will be used
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        print("Action: Mocking asyncio.wait_for to immediately raise TimeoutError...")
        
        # Mock asyncio.wait_for to immediately raise TimeoutError
        async def mock_wait_for_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_timeout):
            with pytest.raises(FirstTokenTimeoutError) as exc_info:
                async for chunk in stream_kiro_to_openai_internal(
                    mock_http_client, mock_response, "test-model",
                    mock_model_cache, mock_auth_manager,
                    first_token_timeout=30  # Value doesn't matter, wait_for is mocked
                ):
                    pass
        
        print(f"Caught exception: {exc_info.value}")
        print("✓ FirstTokenTimeoutError was propagated for retry logic")
        
        # Verify response was closed
        mock_response.aclose.assert_called()
        print("✓ response.aclose() was called")
    
    @pytest.mark.asyncio
    async def test_first_token_timeout_logged_with_correct_format(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that first token timeout is logged with [FirstTokenTimeout] prefix.
        Goal: Ensure consistent logging format for first token timeout.
        """
        import asyncio
        from kiro.streaming_openai import FirstTokenTimeoutError, stream_kiro_to_openai_internal
        
        print("Setup: Mock response with timeout...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        async def mock_wait_for_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        print("Action: Running streaming with timeout and checking logs...")
        
        with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_timeout):
            with patch('kiro.streaming_openai.logger') as mock_logger:
                try:
                    async for chunk in stream_kiro_to_openai_internal(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager,
                        first_token_timeout=15
                    ):
                        pass
                except FirstTokenTimeoutError:
                    pass
                
                print("Check: logger.warning should be called with [FirstTokenTimeout]...")
                warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                print(f"Warning calls: {warning_calls}")
                
                assert any("FirstTokenTimeout" in call for call in warning_calls), \
                    f"[FirstTokenTimeout] not found in warning logs: {warning_calls}"
                print("✓ [FirstTokenTimeout] prefix found in logs")
    
    @pytest.mark.asyncio
    async def test_first_token_timeout_includes_timeout_value(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that first token timeout log includes the timeout value.
        Goal: Ensure timeout value is visible in logs for debugging.
        """
        import asyncio
        from kiro.streaming_openai import FirstTokenTimeoutError, stream_kiro_to_openai_internal
        
        print("Setup: Mock response with timeout...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        async def mock_wait_for_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        custom_timeout = 25.0
        
        print(f"Action: Running streaming with custom timeout={custom_timeout}...")
        
        with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_timeout):
            with patch('kiro.streaming_openai.logger') as mock_logger:
                try:
                    async for chunk in stream_kiro_to_openai_internal(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager,
                        first_token_timeout=custom_timeout
                    ):
                        pass
                except FirstTokenTimeoutError:
                    pass
                
                print("Check: logger.warning should include timeout value...")
                warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                print(f"Warning calls: {warning_calls}")
                
                assert any(str(custom_timeout) in call for call in warning_calls), \
                    f"Timeout value {custom_timeout} not found in warning logs: {warning_calls}"
                print(f"✓ Timeout value {custom_timeout} found in logs")
    
    @pytest.mark.asyncio
    async def test_first_token_received_logged_on_success(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that successful first token receipt is logged.
        Goal: Ensure debug log shows when first token is received.
        """
        from kiro.streaming_openai import stream_kiro_to_openai_internal
        
        print("Setup: Mock response with successful first token...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes():
            yield b'{"content":"Hello"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Hello"}]
        mock_parser.get_tool_calls.return_value = []
        
        print("Action: Running streaming and checking debug logs...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                with patch('kiro.streaming_openai.logger') as mock_logger:
                    chunks = []
                    async for chunk in stream_kiro_to_openai_internal(
                        mock_http_client, mock_response, "test-model",
                        mock_model_cache, mock_auth_manager,
                        first_token_timeout=15
                    ):
                        chunks.append(chunk)
                    
                    print(f"Received {len(chunks)} chunks")
                    print("Check: logger.debug should be called with 'First token received'...")
                    debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
                    print(f"Debug calls: {debug_calls}")
                    
                    assert any("First token received" in call for call in debug_calls), \
                        f"'First token received' not found in debug logs: {debug_calls}"
                    print("✓ 'First token received' found in debug logs")


class TestStreamWithFirstTokenRetry:
    """Tests for stream_with_first_token_retry function."""
    
    @pytest.mark.asyncio
    async def test_retry_on_first_token_timeout(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that request is retried on first token timeout.
        Goal: Ensure retry logic works for first token timeout.
        """
        import asyncio
        from kiro.streaming_openai import stream_with_first_token_retry, FirstTokenTimeoutError
        
        print("Setup: Mock make_request that succeeds on second attempt...")
        
        mock_response_success = AsyncMock()
        mock_response_success.status_code = 200
        mock_response_success.aclose = AsyncMock()
        
        async def mock_aiter_bytes_success():
            yield b'{"content":"Success"}'
        
        mock_response_success.aiter_bytes = mock_aiter_bytes_success
        
        call_count = 0
        
        async def mock_make_request():
            nonlocal call_count
            call_count += 1
            print(f"make_request called (attempt {call_count})")
            return mock_response_success
        
        mock_parser = MagicMock()
        mock_parser.feed.return_value = [{"type": "content", "data": "Success"}]
        mock_parser.get_tool_calls.return_value = []
        
        # First call raises timeout, second succeeds
        timeout_raised = False
        
        async def mock_wait_for_with_retry(coro, timeout):
            nonlocal timeout_raised
            if not timeout_raised:
                timeout_raised = True
                raise asyncio.TimeoutError()
            return await coro
        
        print("Action: Running stream_with_first_token_retry...")
        
        with patch('kiro.streaming_openai.AwsEventStreamParser', return_value=mock_parser):
            with patch('kiro.streaming_openai.parse_bracket_tool_calls', return_value=[]):
                with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_with_retry):
                    chunks = []
                    async for chunk in stream_with_first_token_retry(
                        mock_make_request,
                        mock_http_client,
                        "test-model",
                        mock_model_cache,
                        mock_auth_manager,
                        max_retries=3,
                        first_token_timeout=15
                    ):
                        chunks.append(chunk)
        
        print(f"Received {len(chunks)} chunks")
        print(f"make_request was called {call_count} times")
        
        assert call_count == 2, f"Expected 2 calls (1 timeout + 1 success), got {call_count}"
        assert len(chunks) > 0, "Should receive chunks after retry"
        print("✓ Retry logic worked correctly")
    
    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises_504(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that 504 is raised after all retries exhausted.
        Goal: Ensure proper error handling when model never responds.
        """
        import asyncio
        from fastapi import HTTPException
        from kiro.streaming_openai import stream_with_first_token_retry
        
        print("Setup: Mock make_request that always times out...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        call_count = 0
        
        async def mock_make_request():
            nonlocal call_count
            call_count += 1
            print(f"make_request called (attempt {call_count})")
            return mock_response
        
        async def mock_wait_for_always_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        max_retries = 3
        
        print(f"Action: Running stream_with_first_token_retry with max_retries={max_retries}...")
        
        with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_always_timeout):
            with pytest.raises(HTTPException) as exc_info:
                async for chunk in stream_with_first_token_retry(
                    mock_make_request,
                    mock_http_client,
                    "test-model",
                    mock_model_cache,
                    mock_auth_manager,
                    max_retries=max_retries,
                    first_token_timeout=15
                ):
                    pass
        
        print(f"Caught HTTPException: {exc_info.value.status_code} - {exc_info.value.detail}")
        print(f"make_request was called {call_count} times")
        
        print(f"Сравниваем status_code: Ожидалось 504, Получено {exc_info.value.status_code}")
        assert exc_info.value.status_code == 504
        print(f"Сравниваем call_count: Ожидалось {max_retries}, Получено {call_count}")
        assert call_count == max_retries
        assert "15" in exc_info.value.detail, "Timeout value should be in error message"
        print("✓ 504 raised after all retries exhausted")
    
    @pytest.mark.asyncio
    async def test_retry_logs_attempt_number(self, mock_http_client, mock_model_cache, mock_auth_manager):
        """
        What it does: Verifies that retry attempts are logged with attempt number.
        Goal: Ensure logs show which attempt failed.
        """
        import asyncio
        from fastapi import HTTPException
        from kiro.streaming_openai import stream_with_first_token_retry
        
        print("Setup: Mock make_request that always times out...")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aclose = AsyncMock()
        
        async def mock_aiter_bytes():
            yield b'{"content":"test"}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        async def mock_make_request():
            return mock_response
        
        async def mock_wait_for_always_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        print("Action: Running stream_with_first_token_retry and checking logs...")
        
        with patch('kiro.streaming_openai.asyncio.wait_for', side_effect=mock_wait_for_always_timeout):
            with patch('kiro.streaming_openai.logger') as mock_logger:
                try:
                    async for chunk in stream_with_first_token_retry(
                        mock_make_request,
                        mock_http_client,
                        "test-model",
                        mock_model_cache,
                        mock_auth_manager,
                        max_retries=3,
                        first_token_timeout=15
                    ):
                        pass
                except HTTPException:
                    pass
                
                print("Check: logger.warning should include attempt numbers...")
                warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                print(f"Warning calls: {warning_calls}")
                
                # Should have warnings for attempts 1/3, 2/3, 3/3
                assert any("1/3" in call or "2/3" in call or "3/3" in call for call in warning_calls), \
                    f"Attempt numbers not found in warning logs: {warning_calls}"
                print("✓ Attempt numbers found in logs")
