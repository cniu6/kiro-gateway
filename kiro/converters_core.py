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
Core converters for transforming API formats to Kiro format.

This module contains shared logic used by both OpenAI and Anthropic converters:
- Text content extraction from various formats
- Message merging and processing
- Kiro payload building
- Tool processing and sanitization

The core layer provides a unified interface that API-specific adapters use
to convert their formats to Kiro API format.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from kiro.config import (
    TOOL_DESCRIPTION_MAX_LENGTH,
    FAKE_REASONING_ENABLED,
    FAKE_REASONING_MAX_TOKENS,
)


# ==================================================================================================
# Data Classes for Unified Message Format
# ==================================================================================================

@dataclass
class UnifiedMessage:
    """
    Unified message format used internally by converters.
    
    This format is API-agnostic and can be created from both OpenAI and Anthropic formats.
    
    Attributes:
        role: Message role (user, assistant, system)
        content: Text content or list of content blocks
        tool_calls: List of tool calls (for assistant messages)
        tool_results: List of tool results (for user messages with tool responses)
        images: List of image data (for user messages with images)
    """
    role: str
    content: Any = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None


@dataclass
class UnifiedTool:
    """
    Unified tool format used internally by converters.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON Schema for tool parameters
    """
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None


@dataclass
class KiroPayloadResult:
    """
    Result of building Kiro payload.
    
    Attributes:
        payload: The complete Kiro API payload
        tool_documentation: Documentation for tools with long descriptions (to add to system prompt)
    """
    payload: Dict[str, Any]
    tool_documentation: str = ""


# ==================================================================================================
# Text Content Extraction
# ==================================================================================================

def extract_text_content(content: Any) -> str:
    """
    Extracts text content from various formats.
    
    Supports multiple content formats used by different APIs:
    - String: "Hello, world!"
    - List of content blocks: [{"type": "text", "text": "Hello"}]
    - None: empty message
    
    Args:
        content: Content in any supported format
    
    Returns:
        Extracted text or empty string
    
    Example:
        >>> extract_text_content("Hello")
        'Hello'
        >>> extract_text_content([{"type": "text", "text": "World"}])
        'World'
        >>> extract_text_content(None)
        ''
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif "text" in item and item.get("type") not in ("image", "image_url"):
                    text_parts.append(item["text"])
            elif isinstance(item, str):
                text_parts.append(item)
        return "".join(text_parts)
    return str(content)


def extract_images_from_content(content: Any) -> List[Dict[str, Any]]:
    """
    Extracts image data from message content.
    
    Supports multiple image formats:
    - OpenAI format: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    - Anthropic format: {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "..."}}
    
    Args:
        content: Content in any supported format
    
    Returns:
        List of image data in unified format:
        [{"media_type": "image/jpeg", "data": "base64_data"}]
    """
    images = []
    
    if not isinstance(content, list):
        return images
    
    for item in content:
        if not isinstance(item, dict):
            continue
        
        item_type = item.get("type")
        
        # OpenAI format: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        if item_type == "image_url":
            image_url = item.get("image_url", {})
            url = image_url.get("url", "") if isinstance(image_url, dict) else ""
            
            if url.startswith("data:"):
                # Parse data URL: data:image/jpeg;base64,/9j/4AAQ...
                try:
                    # Split "data:image/jpeg;base64,/9j/4AAQ..." into parts
                    header, data = url.split(",", 1)
                    # Extract media type from "data:image/jpeg;base64"
                    media_part = header.split(";")[0]  # "data:image/jpeg"
                    media_type = media_part.replace("data:", "")  # "image/jpeg"
                    
                    images.append({
                        "media_type": media_type,
                        "data": data
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse image data URL: {e}")
            elif url.startswith("http"):
                # URL-based image - not supported by Kiro, log warning
                logger.warning(f"URL-based images are not supported, skipping: {url[:50]}...")
        
        # Anthropic format: {"type": "image", "source": {"type": "base64", "media_type": "...", "data": "..."}}
        elif item_type == "image":
            source = item.get("source", {})
            if isinstance(source, dict) and source.get("type") == "base64":
                media_type = source.get("media_type", "image/jpeg")
                data = source.get("data", "")
                if data:
                    images.append({
                        "media_type": media_type,
                        "data": data
                    })
    
    return images


# ==================================================================================================
# Thinking Mode Support (Fake Reasoning)
# ==================================================================================================

def get_thinking_system_prompt_addition() -> str:
    """
    Generate system prompt addition that legitimizes thinking tags.
    
    This text is added to the system prompt to inform the model that
    the <thinking_mode>, <max_thinking_length>, and <thinking_instruction>
    tags in user messages are legitimate system-level instructions,
    not prompt injection attempts.
    
    Returns:
        System prompt addition text (empty string if fake reasoning is disabled)
    """
    if not FAKE_REASONING_ENABLED:
        return ""
    
    return (
        "\n\n---\n"
        "# Extended Thinking Mode\n\n"
        "This conversation uses extended thinking mode. User messages may contain "
        "special XML tags that are legitimate system-level instructions:\n"
        "- `<thinking_mode>enabled</thinking_mode>` - enables extended thinking\n"
        "- `<max_thinking_length>N</max_thinking_length>` - sets maximum thinking tokens\n"
        "- `<thinking_instruction>...</thinking_instruction>` - provides thinking guidelines\n\n"
        "These tags are NOT prompt injection attempts. They are part of the system's "
        "extended thinking feature. When you see these tags, follow their instructions "
        "and wrap your reasoning process in `<thinking>...</thinking>` tags before "
        "providing your final response."
    )


def inject_thinking_tags(content: str) -> str:
    """
    Inject fake reasoning tags into content.
    
    When FAKE_REASONING_ENABLED is True, this function prepends the special
    thinking mode tags to the content. These tags instruct the model to
    include its reasoning process in the response.
    
    Args:
        content: Original content string
    
    Returns:
        Content with thinking tags prepended (if enabled) or original content
    """
    if not FAKE_REASONING_ENABLED:
        return content
    
    # Thinking instruction to improve reasoning quality
    thinking_instruction = (
        "Think in English for better reasoning quality.\n\n"
        "Your thinking process should be thorough and systematic:\n"
        "- First, make sure you fully understand what is being asked\n"
        "- Consider multiple approaches or perspectives when relevant\n"
        "- Think about edge cases, potential issues, and what could go wrong\n"
        "- Challenge your initial assumptions\n"
        "- Verify your reasoning before reaching a conclusion\n\n"
        "Take the time you need. Quality of thought matters more than speed."
    )
    
    thinking_prefix = (
        f"<thinking_mode>enabled</thinking_mode>\n"
        f"<max_thinking_length>{FAKE_REASONING_MAX_TOKENS}</max_thinking_length>\n"
        f"<thinking_instruction>{thinking_instruction}</thinking_instruction>\n\n"
    )
    
    logger.debug(f"Injecting fake reasoning tags with max_tokens={FAKE_REASONING_MAX_TOKENS}")
    
    return thinking_prefix + content


# ==================================================================================================
# JSON Schema Sanitization
# ==================================================================================================

def sanitize_json_schema(schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes JSON Schema from fields that Kiro API doesn't accept.
    
    Kiro API returns 400 "Improperly formed request" error if:
    - required is an empty array []
    - additionalProperties is present in schema
    - $schema field is present
    - title field is present in nested schemas
    - anyOf with complex types (simplify to first option)
    
    This function recursively processes the schema and removes problematic fields.
    
    Args:
        schema: JSON Schema to sanitize
    
    Returns:
        Sanitized copy of schema
    """
    if not schema:
        return {}
    
    # Fields that Kiro API doesn't accept
    SKIP_FIELDS = {
        "additionalProperties",
        "$schema",
        "title",  # Kiro doesn't like title in nested schemas
        "default",  # Some APIs send default values
    }
    
    result = {}
    
    for key, value in schema.items():
        # Skip empty required arrays
        if key == "required" and isinstance(value, list) and len(value) == 0:
            continue
        
        # Skip fields that Kiro API doesn't support
        if key in SKIP_FIELDS:
            continue
        
        # Handle anyOf - Kiro may not support complex union types
        # Simplify by taking the first non-null option
        if key == "anyOf" and isinstance(value, list):
            # Find first non-null type
            for option in value:
                if isinstance(option, dict):
                    # Skip {"type": "null"} or {"not": {}}
                    if option.get("type") == "null" or "not" in option:
                        continue
                    # Use this option's properties
                    sanitized_option = sanitize_json_schema(option)
                    result.update(sanitized_option)
                    break
            continue
        
        # Recursively process nested objects
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                prop_name: sanitize_json_schema(prop_value) if isinstance(prop_value, dict) else prop_value
                for prop_name, prop_value in value.items()
            }
        elif isinstance(value, dict):
            result[key] = sanitize_json_schema(value)
        elif isinstance(value, list):
            # Process lists (e.g., oneOf, allOf)
            result[key] = [
                sanitize_json_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


# ==================================================================================================
# Tool Processing
# ==================================================================================================

def process_tools_with_long_descriptions(
    tools: Optional[List[UnifiedTool]]
) -> Tuple[Optional[List[UnifiedTool]], str]:
    """
    Processes tools with long descriptions.
    
    Kiro API has a limit on description length in toolSpecification.
    If description exceeds the limit, full description is moved to system prompt,
    and a reference to documentation remains in the tool.
    
    Args:
        tools: List of tools in unified format
    
    Returns:
        Tuple of:
        - List of tools with processed descriptions (or None if tools is empty)
        - String with documentation to add to system prompt (empty if all descriptions are short)
    """
    if not tools:
        return None, ""
    
    # If limit is disabled (0), return tools unchanged
    if TOOL_DESCRIPTION_MAX_LENGTH <= 0:
        return tools, ""
    
    tool_documentation_parts = []
    processed_tools = []
    
    for tool in tools:
        description = tool.description or ""
        
        if len(description) <= TOOL_DESCRIPTION_MAX_LENGTH:
            # Description is short - leave as is
            processed_tools.append(tool)
        else:
            # Description is too long - move to system prompt
            logger.debug(
                f"Tool '{tool.name}' has long description ({len(description)} chars > {TOOL_DESCRIPTION_MAX_LENGTH}), "
                f"moving to system prompt"
            )
            
            # Create documentation for system prompt
            tool_documentation_parts.append(f"## Tool: {tool.name}\n\n{description}")
            
            # Create copy of tool with reference description
            reference_description = f"[Full documentation in system prompt under '## Tool: {tool.name}']"
            
            processed_tool = UnifiedTool(
                name=tool.name,
                description=reference_description,
                input_schema=tool.input_schema
            )
            processed_tools.append(processed_tool)
    
    # Form final documentation
    tool_documentation = ""
    if tool_documentation_parts:
        tool_documentation = (
            "\n\n---\n"
            "# Tool Documentation\n"
            "The following tools have detailed documentation that couldn't fit in the tool definition.\n\n"
            + "\n\n---\n\n".join(tool_documentation_parts)
        )
    
    return processed_tools if processed_tools else None, tool_documentation


def convert_tools_to_kiro_format(tools: Optional[List[UnifiedTool]]) -> List[Dict[str, Any]]:
    """
    Converts unified tools to Kiro API format.
    
    Args:
        tools: List of tools in unified format
    
    Returns:
        List of tools in Kiro toolSpecification format
    """
    if not tools:
        return []
    
    kiro_tools = []
    for tool in tools:
        # Sanitize parameters from fields that Kiro API doesn't accept
        sanitized_params = sanitize_json_schema(tool.input_schema)
        
        # Kiro API requires non-empty description
        description = tool.description
        if not description or not description.strip():
            description = f"Tool: {tool.name}"
        
        kiro_tools.append({
            "toolSpecification": {
                "name": tool.name,
                "description": description,
                "inputSchema": {"json": sanitized_params}
            }
        })
    
    return kiro_tools


# ==================================================================================================
# Tool Results and Tool Uses Extraction
# ==================================================================================================

def convert_tool_results_to_kiro_format(tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts unified tool results to Kiro API format.
    
    Unified format: {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    Kiro format: {"content": [{"text": "..."}], "status": "success", "toolUseId": "..."}
    
    Args:
        tool_results: List of tool results in unified format
    
    Returns:
        List of tool results in Kiro format
    """
    kiro_results = []
    
    for result in tool_results:
        # Check if already in Kiro format (has "toolUseId" key)
        if "toolUseId" in result:
            kiro_results.append(result)
            continue
        
        # Convert from unified format
        content = result.get("content", "")
        if isinstance(content, str):
            content_text = content
        else:
            content_text = extract_text_content(content)
        
        # Ensure content is not empty - Kiro API requires non-empty content
        if not content_text:
            content_text = "(empty result)"
        
        kiro_results.append({
            "content": [{"text": content_text}],
            "status": "success",
            "toolUseId": result.get("tool_use_id", result.get("toolUseId", ""))
        })
    
    return kiro_results


def extract_tool_results_from_content(content: Any) -> List[Dict[str, Any]]:
    """
    Extracts tool results from message content.
    
    Looks for content blocks with type="tool_result" and converts them
    to Kiro API format.
    
    Args:
        content: Message content (can be a list of content blocks)
    
    Returns:
        List of tool results in Kiro format
    """
    tool_results = []
    
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_results.append({
                    "content": [{"text": extract_text_content(item.get("content", "")) or "(empty result)"}],
                    "status": "success",
                    "toolUseId": item.get("tool_use_id", "")
                })
    
    return tool_results


def extract_tool_uses_from_message(
    content: Any,
    tool_calls: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Extracts tool uses from assistant message.
    
    Looks for tool calls in both:
    - tool_calls field (OpenAI format)
    - content blocks with type="tool_use" (Anthropic format)
    
    Args:
        content: Message content
        tool_calls: List of tool calls (OpenAI format)
    
    Returns:
        List of tool uses in Kiro format
    """
    tool_uses = []
    
    # From tool_calls field (OpenAI format or unified format from Anthropic)
    if tool_calls:
        for tc in tool_calls:
            if isinstance(tc, dict):
                func = tc.get("function", {})
                arguments = func.get("arguments", "{}")
                # Handle both string (OpenAI) and dict (Anthropic unified) formats
                if isinstance(arguments, str):
                    input_data = json.loads(arguments) if arguments else {}
                else:
                    input_data = arguments if arguments else {}
                tool_uses.append({
                    "name": func.get("name", ""),
                    "input": input_data,
                    "toolUseId": tc.get("id", "")
                })
    
    # From content blocks (Anthropic format)
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_uses.append({
                    "name": item.get("name", ""),
                    "input": item.get("input", {}),
                    "toolUseId": item.get("id", "")
                })
    
    return tool_uses


# ==================================================================================================
# Message Merging
# ==================================================================================================

def strip_all_tool_content(messages: List[UnifiedMessage]) -> Tuple[List[UnifiedMessage], bool]:
    """
    Strips ALL tool-related content from messages.
    
    This is used when no tools are defined in the request. Kiro API rejects
    requests that have toolResults but no tools defined.
    
    Args:
        messages: List of messages in unified format
    
    Returns:
        Tuple of:
        - List of messages with all tool content stripped
        - Boolean indicating whether any tool content was stripped
    """
    if not messages:
        return [], False
    
    result = []
    total_tool_calls_stripped = 0
    total_tool_results_stripped = 0
    
    for msg in messages:
        # Check if this message has any tool content
        has_tool_calls = bool(msg.tool_calls)
        has_tool_results = bool(msg.tool_results)
        
        if has_tool_calls or has_tool_results:
            if has_tool_calls:
                total_tool_calls_stripped += len(msg.tool_calls)
            if has_tool_results:
                total_tool_results_stripped += len(msg.tool_results)
            
            # Create a copy of the message without tool content
            cleaned_msg = UnifiedMessage(
                role=msg.role,
                content=msg.content,
                tool_calls=None,
                tool_results=None
            )
            result.append(cleaned_msg)
        else:
            result.append(msg)
    
    had_tool_content = total_tool_calls_stripped > 0 or total_tool_results_stripped > 0
    
    # Log summary once (DEBUG level - this is normal for clients like Cline/Roo)
    if had_tool_content:
        logger.debug(
            f"Stripped tool content (no tools defined): "
            f"{total_tool_calls_stripped} tool_calls, {total_tool_results_stripped} tool_results"
        )
    
    return result, had_tool_content


def ensure_assistant_before_tool_results(messages: List[UnifiedMessage]) -> Tuple[List[UnifiedMessage], bool]:
    """
    Ensures that messages with tool_results have a preceding assistant message with tool_calls.
    
    Kiro API requires that when toolResults are present, there must be a preceding
    assistantResponseMessage with toolUses. Some clients (like Cline/Roo) may send
    truncated conversations where the assistant message is missing.
    
    Since we don't know the original tool name and arguments when the assistant message
    is missing, we cannot create a valid synthetic assistant message. Instead, we strip
    the tool_results from such messages to avoid Kiro API rejection.
    
    Args:
        messages: List of messages in unified format
    
    Returns:
        Tuple of:
        - List of messages with orphaned tool_results stripped
        - Boolean indicating whether any tool_results were stripped (used to skip thinking tag injection)
    """
    if not messages:
        return [], False
    
    result = []
    stripped_any_tool_results = False
    
    for msg in messages:
        # Check if this message has tool_results
        if msg.tool_results:
            # Check if the previous message is an assistant with tool_calls
            has_preceding_assistant = (
                result and
                result[-1].role == "assistant" and
                result[-1].tool_calls
            )
            
            if not has_preceding_assistant:
                # We cannot create a valid synthetic assistant message because we don't know
                # the original tool name and arguments. Kiro API validates tool names.
                # Strip the tool_results to avoid "Improperly formed request" error.
                logger.warning(
                    f"Stripping {len(msg.tool_results)} orphaned tool_results "
                    f"(no preceding assistant message with tool_calls). "
                    f"Tool IDs: {[tr.get('tool_use_id', 'unknown') for tr in msg.tool_results]}"
                )
                
                # Create a copy of the message without tool_results
                cleaned_msg = UnifiedMessage(
                    role=msg.role,
                    content=msg.content,
                    tool_calls=msg.tool_calls,
                    tool_results=None  # Strip orphaned tool_results
                )
                result.append(cleaned_msg)
                stripped_any_tool_results = True
                continue
        
        result.append(msg)
    
    return result, stripped_any_tool_results


def merge_adjacent_messages(messages: List[UnifiedMessage]) -> List[UnifiedMessage]:
    """
    Merges adjacent messages with the same role.
    
    Kiro API does not accept multiple consecutive messages from the same role.
    This function merges such messages into one.
    
    Args:
        messages: List of messages in unified format
    
    Returns:
        List of messages with merged adjacent messages
    """
    if not messages:
        return []
    
    merged = []
    # Statistics for summary logging
    merge_counts = {"user": 0, "assistant": 0}
    total_tool_calls_merged = 0
    total_tool_results_merged = 0
    
    for msg in messages:
        if not merged:
            merged.append(msg)
            continue
        
        last = merged[-1]
        if msg.role == last.role:
            # Merge content
            if isinstance(last.content, list) and isinstance(msg.content, list):
                last.content = last.content + msg.content
            elif isinstance(last.content, list):
                last.content = last.content + [{"type": "text", "text": extract_text_content(msg.content)}]
            elif isinstance(msg.content, list):
                last.content = [{"type": "text", "text": extract_text_content(last.content)}] + msg.content
            else:
                last_text = extract_text_content(last.content)
                current_text = extract_text_content(msg.content)
                last.content = f"{last_text}\n{current_text}"
            
            # Merge tool_calls for assistant messages
            if msg.role == "assistant" and msg.tool_calls:
                if last.tool_calls is None:
                    last.tool_calls = []
                last.tool_calls = list(last.tool_calls) + list(msg.tool_calls)
                total_tool_calls_merged += len(msg.tool_calls)
            
            # Merge tool_results for user messages
            if msg.role == "user" and msg.tool_results:
                if last.tool_results is None:
                    last.tool_results = []
                last.tool_results = list(last.tool_results) + list(msg.tool_results)
                total_tool_results_merged += len(msg.tool_results)
            
            # Count merges by role
            if msg.role in merge_counts:
                merge_counts[msg.role] += 1
        else:
            merged.append(msg)
    
    # Log summary if any merges occurred
    total_merges = sum(merge_counts.values())
    if total_merges > 0:
        parts = []
        for role, count in merge_counts.items():
            if count > 0:
                parts.append(f"{count} {role}")
        merge_summary = ", ".join(parts)
        
        extras = []
        if total_tool_calls_merged > 0:
            extras.append(f"{total_tool_calls_merged} tool_calls")
        if total_tool_results_merged > 0:
            extras.append(f"{total_tool_results_merged} tool_results")
        
        if extras:
            logger.debug(f"Merged {total_merges} adjacent messages ({merge_summary}), including {', '.join(extras)}")
        else:
            logger.debug(f"Merged {total_merges} adjacent messages ({merge_summary})")
    
    return merged


# ==================================================================================================
# Kiro History Building
# ==================================================================================================

def build_kiro_history(messages: List[UnifiedMessage], model_id: str) -> List[Dict[str, Any]]:
    """
    Builds history array for Kiro API from unified messages.
    
    Kiro API expects alternating userInputMessage and assistantResponseMessage.
    This function converts unified format to Kiro format.
    
    Args:
        messages: List of messages in unified format
        model_id: Internal Kiro model ID
    
    Returns:
        List of dictionaries for history field in Kiro API
    """
    history = []
    
    for msg in messages:
        if msg.role == "user":
            content = extract_text_content(msg.content)
            
            user_input = {
                "content": content,
                "modelId": model_id,
                "origin": "AI_EDITOR",
            }
            
            # Build userInputMessageContext
            user_input_context = {}
            
            # Process images - convert to Kiro format
            images = msg.images or extract_images_from_content(msg.content)
            if images:
                kiro_images = []
                for img in images:
                    kiro_images.append({
                        "format": img.get("media_type", "image/jpeg").split("/")[-1],  # "jpeg", "png", etc.
                        "source": {
                            "bytes": img.get("data", "")
                        }
                    })
                if kiro_images:
                    user_input_context["images"] = kiro_images
            
            # Process tool_results - convert to Kiro format
            tool_results = msg.tool_results or extract_tool_results_from_content(msg.content)
            if tool_results:
                kiro_tool_results = convert_tool_results_to_kiro_format(tool_results)
                if kiro_tool_results:
                    user_input_context["toolResults"] = kiro_tool_results
            
            # Add context if not empty
            if user_input_context:
                user_input["userInputMessageContext"] = user_input_context
            
            history.append({"userInputMessage": user_input})
            
        elif msg.role == "assistant":
            content = extract_text_content(msg.content)
            
            assistant_response = {"content": content}
            
            # Process tool_calls
            tool_uses = extract_tool_uses_from_message(msg.content, msg.tool_calls)
            if tool_uses:
                assistant_response["toolUses"] = tool_uses
            
            history.append({"assistantResponseMessage": assistant_response})
    
    return history


# ==================================================================================================
# Main Payload Building
# ==================================================================================================

def build_kiro_payload(
    messages: List[UnifiedMessage],
    system_prompt: str,
    model_id: str,
    tools: Optional[List[UnifiedTool]],
    conversation_id: str,
    profile_arn: str,
    inject_thinking: bool = True
) -> KiroPayloadResult:
    """
    Builds complete payload for Kiro API from unified data.
    
    This is the main function that assembles the Kiro API payload from
    API-agnostic unified message and tool formats.
    
    Args:
        messages: List of messages in unified format (without system messages)
        system_prompt: Already extracted system prompt
        model_id: Internal Kiro model ID
        tools: List of tools in unified format (or None)
        conversation_id: Unique conversation ID
        profile_arn: AWS CodeWhisperer profile ARN
        inject_thinking: Whether to inject thinking tags (default True)
    
    Returns:
        KiroPayloadResult with payload and tool documentation
    
    Raises:
        ValueError: If there are no messages to send
    """
    # Process tools with long descriptions
    processed_tools, tool_documentation = process_tools_with_long_descriptions(tools)
    
    # Add tool documentation to system prompt if present
    full_system_prompt = system_prompt
    if tool_documentation:
        full_system_prompt = full_system_prompt + tool_documentation if full_system_prompt else tool_documentation.strip()
    
    # Add thinking mode legitimization to system prompt if enabled
    thinking_system_addition = get_thinking_system_prompt_addition()
    if thinking_system_addition:
        full_system_prompt = full_system_prompt + thinking_system_addition if full_system_prompt else thinking_system_addition.strip()
    
    # If no tools are defined, strip ALL tool-related content from messages
    # Kiro API rejects requests with toolResults but no tools
    if not tools:
        messages_without_tools, had_tool_content = strip_all_tool_content(messages)
        messages_with_assistants = messages_without_tools
        stripped_tool_results = had_tool_content
    else:
        # Ensure assistant messages exist before tool_results (Kiro API requirement)
        # Also returns flag if any tool_results were stripped (to skip thinking tag injection)
        messages_with_assistants, stripped_tool_results = ensure_assistant_before_tool_results(messages)
    
    # Merge adjacent messages with the same role
    merged_messages = merge_adjacent_messages(messages_with_assistants)
    
    if not merged_messages:
        raise ValueError("No messages to send")
    
    # Build history (all messages except the last one)
    history_messages = merged_messages[:-1] if len(merged_messages) > 1 else []
    
    # If there's a system prompt, add it to the first user message in history
    if full_system_prompt and history_messages:
        first_msg = history_messages[0]
        if first_msg.role == "user":
            original_content = extract_text_content(first_msg.content)
            first_msg.content = f"{full_system_prompt}\n\n{original_content}"
    
    history = build_kiro_history(history_messages, model_id)
    
    # Current message (the last one)
    current_message = merged_messages[-1]
    current_content = extract_text_content(current_message.content)
    
    # If system prompt exists but history is empty - add to current message
    if full_system_prompt and not history:
        current_content = f"{full_system_prompt}\n\n{current_content}"
    
    # If current message is assistant, need to add it to history
    # and create user message "Continue"
    if current_message.role == "assistant":
        history.append({
            "assistantResponseMessage": {
                "content": current_content
            }
        })
        current_content = "Continue"
    
    # If content is empty - use "Continue"
    if not current_content:
        current_content = "Continue"
    
    # Build user_input_context
    user_input_context = {}
    
    # Add tools if present
    kiro_tools = convert_tools_to_kiro_format(processed_tools)
    if kiro_tools:
        user_input_context["tools"] = kiro_tools
    
    # Process images in current message - convert to Kiro format
    images = current_message.images or extract_images_from_content(current_message.content)
    if images:
        kiro_images = []
        for img in images:
            kiro_images.append({
                "format": img.get("media_type", "image/jpeg").split("/")[-1],  # "jpeg", "png", etc.
                "source": {
                    "bytes": img.get("data", "")
                }
            })
        if kiro_images:
            user_input_context["images"] = kiro_images
            logger.debug(f"Added {len(kiro_images)} images to current message")
    
    # Process tool_results in current message
    tool_results = current_message.tool_results or extract_tool_results_from_content(current_message.content)
    if tool_results:
        kiro_tool_results = convert_tool_results_to_kiro_format(tool_results)
        if kiro_tool_results:
            user_input_context["toolResults"] = kiro_tool_results
    
    # Inject thinking tags if enabled (only for the current/last user message)
    if inject_thinking and current_message.role == "user":
        current_content = inject_thinking_tags(current_content)
    
    # Build userInputMessage
    user_input_message = {
        "content": current_content,
        "modelId": model_id,
        "origin": "AI_EDITOR",
    }
    
    # Add user_input_context if present
    if user_input_context:
        user_input_message["userInputMessageContext"] = user_input_context
    
    # Assemble final payload
    payload = {
        "conversationState": {
            "chatTriggerType": "MANUAL",
            "conversationId": conversation_id,
            "currentMessage": {
                "userInputMessage": user_input_message
            }
        }
    }
    
    # Add history only if not empty
    if history:
        payload["conversationState"]["history"] = history
    
    # Add profileArn
    if profile_arn:
        payload["profileArn"] = profile_arn
    
    return KiroPayloadResult(payload=payload, tool_documentation=tool_documentation)