# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Streaming logic for converting Kiro stream to OpenAI format.

Contains generators for:
- Converting AWS SSE to OpenAI SSE
- Forming streaming chunks
- Processing tool calls in stream
"""

import asyncio
import json
import time
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Awaitable, Optional

import httpx
from fastapi import HTTPException
from loguru import logger

from kiro.parsers import AwsEventStreamParser, parse_bracket_tool_calls, deduplicate_tool_calls
from kiro.utils import generate_completion_id
from kiro.config import (
    FIRST_TOKEN_TIMEOUT,
    FIRST_TOKEN_MAX_RETRIES,
    FAKE_REASONING_ENABLED,
    FAKE_REASONING_HANDLING,
)
from kiro.tokenizer import count_tokens, count_message_tokens, count_tools_tokens
from kiro.thinking_parser import ThinkingParser

if TYPE_CHECKING:
    from kiro.auth import KiroAuthManager
    from kiro.cache import ModelInfoCache

# Import debug_logger for logging
try:
    from kiro.debug_logger import debug_logger
except ImportError:
    debug_logger = None


class FirstTokenTimeoutError(Exception):
    """Exception raised when first token timeout occurs."""
    pass


async def stream_kiro_to_openai_internal(
    client: httpx.AsyncClient,
    response: httpx.Response,
    model: str,
    model_cache: "ModelInfoCache",
    auth_manager: "KiroAuthManager",
    first_token_timeout: float = FIRST_TOKEN_TIMEOUT,
    request_messages: Optional[list] = None,
    request_tools: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    Internal generator for converting Kiro stream to OpenAI format.
    
    Parses AWS SSE stream and converts events to OpenAI chat.completion.chunk.
    Supports tool calls and usage calculation.
    
    IMPORTANT: This function raises FirstTokenTimeoutError if first token
    is not received within first_token_timeout seconds.
    
    Args:
        client: HTTP client (for connection management)
        response: HTTP response with data stream
        model: Model name to include in response
        model_cache: Model cache for getting token limits
        auth_manager: Authentication manager
        first_token_timeout: First token wait timeout (seconds)
        request_messages: Original request messages (for fallback token counting)
        request_tools: Original request tools (for fallback token counting)
    
    Yields:
        Strings in SSE format: "data: {...}\\n\\n" or "data: [DONE]\\n\\n"
    
    Raises:
        FirstTokenTimeoutError: If first token not received within timeout
    
    Example:
        >>> async for chunk in stream_kiro_to_openai_internal(client, response, "claude-sonnet-4", cache, auth):
        ...     print(chunk)
        data: {"id":"chatcmpl-...","object":"chat.completion.chunk",...}
        
        data: [DONE]
    """
    completion_id = generate_completion_id()
    created_time = int(time.time())
    first_chunk = True
    first_token_received = False
    
    parser = AwsEventStreamParser()
    metering_data = None
    context_usage_percentage = None
    full_content = ""
    full_thinking_content = ""  # Accumulated thinking content for non-streaming
    
    streaming_error_occurred = False
    
    # Initialize thinking parser if fake reasoning is enabled
    thinking_parser: Optional[ThinkingParser] = None
    if FAKE_REASONING_ENABLED:
        thinking_parser = ThinkingParser(handling_mode=FAKE_REASONING_HANDLING)
        logger.debug(f"Thinking parser initialized with mode: {FAKE_REASONING_HANDLING}")
    
    try:
        # Create iterator for reading bytes
        byte_iterator = response.aiter_bytes()
        
        # Wait for first chunk with timeout (FIRST_TOKEN_TIMEOUT)
        # This is our business logic for detecting "stuck" requests
        # where the model takes too long to start responding
        try:
            logger.debug(f"Waiting for first token (timeout={first_token_timeout}s)...")
            first_byte_chunk = await asyncio.wait_for(
                byte_iterator.__anext__(),
                timeout=first_token_timeout
            )
            logger.debug("First token received")
        except asyncio.TimeoutError:
            logger.warning(f"[FirstTokenTimeout] Model did not respond within {first_token_timeout}s")
            raise FirstTokenTimeoutError(f"No response within {first_token_timeout} seconds")
        except StopAsyncIteration:
            # Empty response - this is normal, just finish
            logger.debug("Empty response from Kiro API")
            yield "data: [DONE]\n\n"
            return
        
        # Process first chunk
        if debug_logger:
            debug_logger.log_raw_chunk(first_byte_chunk)
        
        events = parser.feed(first_byte_chunk)
        for event in events:
            if event["type"] == "content":
                first_token_received = True
                content = event["data"]
                full_content += content
                
                # Process through thinking parser if enabled
                if thinking_parser:
                    parse_result = thinking_parser.feed(content)
                    
                    # Yield thinking content if any
                    if parse_result.thinking_content:
                        full_thinking_content += parse_result.thinking_content
                        processed_thinking = thinking_parser.process_for_output(
                            parse_result.thinking_content,
                            parse_result.is_first_thinking_chunk,
                            parse_result.is_last_thinking_chunk,
                        )
                        if processed_thinking:
                            # Send as reasoning_content or content based on mode
                            if FAKE_REASONING_HANDLING == "as_reasoning_content":
                                delta = {"reasoning_content": processed_thinking}
                            else:
                                delta = {"content": processed_thinking}
                            
                            if first_chunk:
                                delta["role"] = "assistant"
                                first_chunk = False
                            
                            openai_chunk = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": model,
                                "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                            }
                            
                            chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                            
                            if debug_logger:
                                debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                            
                            yield chunk_text
                    
                    # Yield regular content if any
                    if parse_result.regular_content:
                        delta = {"content": parse_result.regular_content}
                        if first_chunk:
                            delta["role"] = "assistant"
                            first_chunk = False
                        
                        openai_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": model,
                            "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                        }
                        
                        chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                        
                        if debug_logger:
                            debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                        
                        yield chunk_text
                else:
                    # No thinking parser - pass through as-is
                    delta = {"content": content}
                    if first_chunk:
                        delta["role"] = "assistant"
                        first_chunk = False
                    
                    openai_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model,
                        "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                    }
                    
                    chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                    
                    if debug_logger:
                        debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                    
                    yield chunk_text
            
            elif event["type"] == "usage":
                metering_data = event["data"]
            
            elif event["type"] == "context_usage":
                context_usage_percentage = event["data"]
        
        # Continue reading remaining chunks (no longer with first token timeout)
        async for chunk in byte_iterator:
            # Log raw chunk
            if debug_logger:
                debug_logger.log_raw_chunk(chunk)
            
            events = parser.feed(chunk)
            
            for event in events:
                if event["type"] == "content":
                    content = event["data"]
                    full_content += content
                    
                    # Process through thinking parser if enabled
                    if thinking_parser:
                        parse_result = thinking_parser.feed(content)
                        
                        # Yield thinking content if any
                        if parse_result.thinking_content:
                            full_thinking_content += parse_result.thinking_content
                            processed_thinking = thinking_parser.process_for_output(
                                parse_result.thinking_content,
                                parse_result.is_first_thinking_chunk,
                                parse_result.is_last_thinking_chunk,
                            )
                            if processed_thinking:
                                # Send as reasoning_content or content based on mode
                                if FAKE_REASONING_HANDLING == "as_reasoning_content":
                                    delta = {"reasoning_content": processed_thinking}
                                else:
                                    delta = {"content": processed_thinking}
                                
                                if first_chunk:
                                    delta["role"] = "assistant"
                                    first_chunk = False
                                
                                openai_chunk = {
                                    "id": completion_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": model,
                                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                                }
                                
                                chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                                
                                if debug_logger:
                                    debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                                
                                yield chunk_text
                        
                        # Yield regular content if any
                        if parse_result.regular_content:
                            delta = {"content": parse_result.regular_content}
                            if first_chunk:
                                delta["role"] = "assistant"
                                first_chunk = False
                            
                            openai_chunk = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": model,
                                "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                            }
                            
                            chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                            
                            if debug_logger:
                                debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                            
                            yield chunk_text
                    else:
                        # No thinking parser - pass through as-is
                        delta = {"content": content}
                        if first_chunk:
                            delta["role"] = "assistant"
                            first_chunk = False
                        
                        openai_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": model,
                            "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                        }
                        
                        chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                        
                        if debug_logger:
                            debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                        
                        yield chunk_text
                
                elif event["type"] == "usage":
                    metering_data = event["data"]
                
                elif event["type"] == "context_usage":
                    context_usage_percentage = event["data"]
        
        # Finalize thinking parser and yield any remaining content
        if thinking_parser:
            final_result = thinking_parser.finalize()
            
            if final_result.thinking_content:
                full_thinking_content += final_result.thinking_content
                processed_thinking = thinking_parser.process_for_output(
                    final_result.thinking_content,
                    final_result.is_first_thinking_chunk,
                    final_result.is_last_thinking_chunk,
                )
                if processed_thinking:
                    if FAKE_REASONING_HANDLING == "as_reasoning_content":
                        delta = {"reasoning_content": processed_thinking}
                    else:
                        delta = {"content": processed_thinking}
                    
                    if first_chunk:
                        delta["role"] = "assistant"
                        first_chunk = False
                    
                    openai_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model,
                        "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                    }
                    
                    chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                    
                    if debug_logger:
                        debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                    
                    yield chunk_text
            
            if final_result.regular_content:
                delta = {"content": final_result.regular_content}
                if first_chunk:
                    delta["role"] = "assistant"
                    first_chunk = False
                
                openai_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": model,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}]
                }
                
                chunk_text = f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                
                if debug_logger:
                    debug_logger.log_modified_chunk(chunk_text.encode('utf-8'))
                
                yield chunk_text
            
            if thinking_parser.found_thinking_block:
                logger.debug(f"Thinking block processed: {len(full_thinking_content)} chars")
        
        # Check bracket-style tool calls in full content
        bracket_tool_calls = parse_bracket_tool_calls(full_content)
        all_tool_calls = parser.get_tool_calls() + bracket_tool_calls
        all_tool_calls = deduplicate_tool_calls(all_tool_calls)
        
        # Determine finish_reason
        finish_reason = "tool_calls" if all_tool_calls else "stop"
        
        # Count completion_tokens (output) using tiktoken
        completion_tokens = count_tokens(full_content)
        
        # Calculate total_tokens based on context_usage_percentage from Kiro API
        # context_usage shows TOTAL percentage of context usage (input + output)
        total_tokens_from_api = 0
        if context_usage_percentage is not None and context_usage_percentage > 0:
            max_input_tokens = model_cache.get_max_input_tokens(model)
            total_tokens_from_api = int((context_usage_percentage / 100) * max_input_tokens)
        
        # Determine data source and calculate tokens
        if total_tokens_from_api > 0:
            # Use data from Kiro API
            # prompt_tokens (input) = total_tokens - completion_tokens
            prompt_tokens = max(0, total_tokens_from_api - completion_tokens)
            total_tokens = total_tokens_from_api
            prompt_source = "subtraction"
            total_source = "API Kiro"
        else:
            # Fallback: Kiro API didn't return context_usage, use tiktoken
            # Count prompt_tokens from original messages
            # IMPORTANT: Don't apply correction coefficient for prompt_tokens,
            # as it was calibrated for completion_tokens
            prompt_tokens = 0
            if request_messages:
                prompt_tokens += count_message_tokens(request_messages, apply_claude_correction=False)
            if request_tools:
                prompt_tokens += count_tools_tokens(request_tools, apply_claude_correction=False)
            total_tokens = prompt_tokens + completion_tokens
            prompt_source = "tiktoken"
            total_source = "tiktoken"
        
        # Send tool calls if present
        if all_tool_calls:
            logger.debug(f"Processing {len(all_tool_calls)} tool calls for streaming response")
            
            # Add required index field to each tool_call
            # according to OpenAI API specification for streaming
            indexed_tool_calls = []
            for idx, tc in enumerate(all_tool_calls):
                # Extract function with None protection
                func = tc.get("function") or {}
                # Use "or" for protection against explicit None in values
                tool_name = func.get("name") or ""
                tool_args = func.get("arguments") or "{}"
                
                logger.debug(f"Tool call [{idx}] '{tool_name}': id={tc.get('id')}, args_length={len(tool_args)}")
                
                indexed_tc = {
                    "index": idx,
                    "id": tc.get("id"),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tool_name,
                        "arguments": tool_args
                    }
                }
                indexed_tool_calls.append(indexed_tc)
            
            tool_calls_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"tool_calls": indexed_tool_calls},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(tool_calls_chunk, ensure_ascii=False)}\n\n"
        
        # Final chunk with usage
        final_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
        }
        
        if metering_data:
            final_chunk["usage"]["credits_used"] = metering_data
        
        # Log final token values being sent to client
        logger.debug(
            f"[Usage] {model}: "
            f"prompt_tokens={prompt_tokens} ({prompt_source}), "
            f"completion_tokens={completion_tokens} (tiktoken), "
            f"total_tokens={total_tokens} ({total_source})"
        )
        
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
    except FirstTokenTimeoutError:
        # Propagate timeout up for retry
        raise
    except GeneratorExit:
        # Client disconnected - this is normal, don't log as error
        logger.debug("Client disconnected (GeneratorExit)")
        streaming_error_occurred = True
    except Exception as e:
        streaming_error_occurred = True
        # Log exception type and message for better diagnostics
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else "(empty message)"
        logger.error(
            f"Error during streaming: [{error_type}] {error_msg}",
            exc_info=True
        )
        # Propagate error up for proper handling in routes_openai.py
        raise
    finally:
        # Always close response
        try:
            await response.aclose()
        except Exception as close_error:
            logger.debug(f"Error closing response: {close_error}")
        
        if streaming_error_occurred:
            logger.debug("Streaming completed with error")
        else:
            logger.debug("Streaming completed successfully")


async def stream_kiro_to_openai(
    client: httpx.AsyncClient,
    response: httpx.Response,
    model: str,
    model_cache: "ModelInfoCache",
    auth_manager: "KiroAuthManager",
    request_messages: Optional[list] = None,
    request_tools: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    Generator for converting Kiro stream to OpenAI format.
    
    This is a wrapper over stream_kiro_to_openai_internal that does NOT retry.
    Retry logic is implemented in stream_with_first_token_retry.
    
    Args:
        client: HTTP client (for connection management)
        response: HTTP response with data stream
        model: Model name to include in response
        model_cache: Model cache for getting token limits
        auth_manager: Authentication manager
        request_messages: Original request messages (for fallback token counting)
        request_tools: Original request tools (for fallback token counting)
    
    Yields:
        Strings in SSE format: "data: {...}\\n\\n" or "data: [DONE]\\n\\n"
    """
    async for chunk in stream_kiro_to_openai_internal(
        client, response, model, model_cache, auth_manager,
        request_messages=request_messages,
        request_tools=request_tools
    ):
        yield chunk


async def stream_with_first_token_retry(
    make_request: Callable[[], Awaitable[httpx.Response]],
    client: httpx.AsyncClient,
    model: str,
    model_cache: "ModelInfoCache",
    auth_manager: "KiroAuthManager",
    max_retries: int = FIRST_TOKEN_MAX_RETRIES,
    first_token_timeout: float = FIRST_TOKEN_TIMEOUT,
    request_messages: Optional[list] = None,
    request_tools: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    Streaming with automatic retry on first token timeout.
    
    If model doesn't respond within first_token_timeout seconds,
    request is cancelled and a new one is made. Maximum max_retries attempts.
    
    This is seamless for user - they just see a delay,
    but eventually get a response (or error after all attempts).
    
    Args:
        make_request: Function to create new HTTP request
        client: HTTP client
        model: Model name
        model_cache: Model cache
        auth_manager: Authentication manager
        max_retries: Maximum number of attempts
        first_token_timeout: First token wait timeout (seconds)
        request_messages: Original request messages (for fallback token counting)
        request_tools: Original request tools (for fallback token counting)
    
    Yields:
        Strings in SSE format
    
    Raises:
        HTTPException: After exhausting all attempts
    
    Example:
        >>> async def make_req():
        ...     return await http_client.request_with_retry("POST", url, payload, stream=True)
        >>> async for chunk in stream_with_first_token_retry(make_req, client, model, cache, auth):
        ...     print(chunk)
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(max_retries):
        response: Optional[httpx.Response] = None
        try:
            # Make request
            if attempt > 0:
                logger.warning(f"Retry attempt {attempt + 1}/{max_retries} after first token timeout")
            
            response = await make_request()
            
            if response.status_code != 200:
                # Error from API - close response and raise exception
                try:
                    error_content = await response.aread()
                    error_text = error_content.decode('utf-8', errors='replace')
                except Exception:
                    error_text = "Unknown error"
                
                try:
                    await response.aclose()
                except Exception:
                    pass
                
                logger.error(f"Error from Kiro API: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upstream API error: {error_text}"
                )
            
            # Try to stream with first token timeout
            async for chunk in stream_kiro_to_openai_internal(
                client,
                response,
                model,
                model_cache,
                auth_manager,
                first_token_timeout=first_token_timeout,
                request_messages=request_messages,
                request_tools=request_tools
            ):
                yield chunk
            
            # Successfully completed - exit
            return
            
        except FirstTokenTimeoutError as e:
            last_error = e
            logger.warning(
                f"[FirstTokenTimeout] Attempt {attempt + 1}/{max_retries} failed - "
                f"model did not respond within {first_token_timeout}s"
            )
            
            # Close current response if open
            if response:
                try:
                    await response.aclose()
                except Exception:
                    pass
            
            # Continue to next attempt
            continue
            
        except Exception as e:
            # Other errors - no retry, propagate
            logger.error(f"Unexpected error during streaming: {e}", exc_info=True)
            if response:
                try:
                    await response.aclose()
                except Exception:
                    pass
            raise
    
    # All attempts exhausted - raise HTTP error
    logger.error(
        f"[FirstTokenTimeout] All {max_retries} attempts exhausted - "
        f"model never responded within {first_token_timeout}s per attempt"
    )
    raise HTTPException(
        status_code=504,
        detail=f"Model did not respond within {first_token_timeout}s after {max_retries} attempts. Please try again."
    )


async def collect_stream_response(
    client: httpx.AsyncClient,
    response: httpx.Response,
    model: str,
    model_cache: "ModelInfoCache",
    auth_manager: "KiroAuthManager",
    request_messages: Optional[list] = None,
    request_tools: Optional[list] = None
) -> dict:
    """
    Collect full response from streaming stream.
    
    Used for non-streaming mode - collects all chunks
    and forms a single response.
    
    Args:
        client: HTTP client
        response: HTTP response with stream
        model: Model name
        model_cache: Model cache
        auth_manager: Authentication manager
        request_messages: Original request messages (for fallback token counting)
        request_tools: Original request tools (for fallback token counting)
    
    Returns:
        Dictionary with full response in OpenAI chat.completion format
    """
    full_content = ""
    full_reasoning_content = ""
    final_usage = None
    tool_calls = []
    completion_id = generate_completion_id()
    
    async for chunk_str in stream_kiro_to_openai(
        client,
        response,
        model,
        model_cache,
        auth_manager,
        request_messages=request_messages,
        request_tools=request_tools
    ):
        if not chunk_str.startswith("data:"):
            continue
        
        data_str = chunk_str[len("data:"):].strip()
        if not data_str or data_str == "[DONE]":
            continue
        
        try:
            chunk_data = json.loads(data_str)
            
            # Extract data from chunk
            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
            if "content" in delta:
                full_content += delta["content"]
            if "reasoning_content" in delta:
                full_reasoning_content += delta["reasoning_content"]
            if "tool_calls" in delta:
                tool_calls.extend(delta["tool_calls"])
            
            # Save usage from last chunk
            if "usage" in chunk_data:
                final_usage = chunk_data["usage"]
                
        except (json.JSONDecodeError, IndexError):
            continue
    
    # Form final response
    message = {"role": "assistant", "content": full_content}
    if full_reasoning_content:
        message["reasoning_content"] = full_reasoning_content
    if tool_calls:
        # For non-streaming response remove index field from tool_calls,
        # as it's only required for streaming chunks
        cleaned_tool_calls = []
        for tc in tool_calls:
            # Extract function with None protection
            func = tc.get("function") or {}
            cleaned_tc = {
                "id": tc.get("id"),
                "type": tc.get("type", "function"),
                "function": {
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", "{}")
                }
            }
            cleaned_tool_calls.append(cleaned_tc)
        message["tool_calls"] = cleaned_tool_calls
    
    finish_reason = "tool_calls" if tool_calls else "stop"
    
    # Form usage for response
    usage = final_usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    # Log token info for debugging (non-streaming uses same logs from streaming)
    
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": finish_reason
        }],
        "usage": usage
    }