#!/usr/bin/env python3
"""
Claude Code Hook JSON Parser

This script parses JSON data from Claude Code hooks and displays all fields
in a structured, readable format. Useful for debugging and understanding
hook input data structure.

Usage:
  echo '{"field": "value"}' | python hook_json_parser.py

  Or as a hook in Claude Code settings:
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "*",
          "hooks": [
            {
              "type": "command",
              "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/hook_json_parser.py"
            }
          ]
        }
      ]
    }
  }
"""

import json
import re
import sys
from typing import Any, Dict


def normalize_paths_in_json(json_text: str) -> str:
    """
    Normalize Windows paths in JSON text to use forward slashes.
    This helps avoid JSON escape sequence issues with backslashes.

    Args:
        json_text: Raw JSON text that may contain Windows paths

    Returns:
        JSON text with Windows paths normalized to use forward slashes
    """
    # Pattern to match Windows-style paths in JSON strings
    # Matches patterns like: "C:\\Users\\..." or "D:\\path\\..."
    windows_path_pattern = r'"([A-Za-z]:\\\\[^"]*)"'

    def replace_path(match):
        path = match.group(1)
        # Replace double backslashes with forward slashes
        normalized_path = path.replace("\\\\", "/")
        # Also handle single backslashes (in case they exist)
        normalized_path = normalized_path.replace("\\", "/")
        return f'"{normalized_path}"'

    # Apply the replacement
    normalized_text = re.sub(windows_path_pattern, replace_path, json_text)

    # Also handle UNC paths like \\\\server\\share
    unc_pattern = r'"(\\\\\\\\[^"]*)"'

    def replace_unc_path(match):
        path = match.group(1)
        # Replace quadruple backslashes with double forward slashes for UNC paths
        normalized_path = path.replace("\\\\\\\\", "//")
        normalized_path = normalized_path.replace("\\\\", "/")
        normalized_path = normalized_path.replace("\\", "/")
        return f'"{normalized_path}"'

    normalized_text = re.sub(unc_pattern, replace_unc_path, normalized_text)

    return normalized_text


def get_type_info(value: Any) -> str:
    """Get a readable type name for a value."""
    if isinstance(value, str):
        return "str"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, list):
        return f"list[{len(value)}]"
    elif isinstance(value, dict):
        return f"dict[{len(value)}]"
    elif value is None:
        return "null"
    else:
        return type(value).__name__


def format_value(value: Any, max_length: int = 100) -> str:
    """Format a value for display, truncating if necessary."""
    if isinstance(value, str):
        if len(value) > max_length:
            return f'"{value[:max_length]}..."'
        else:
            return f'"{value}"'
    elif isinstance(value, (int, float, bool)):
        return str(value)
    elif value is None:
        return "null"
    elif isinstance(value, (list, dict)):
        # For collections, just show type info
        return f"<{get_type_info(value)}>"
    else:
        return str(value)


def print_json_tree(
    data: Any, prefix: str = "", is_last: bool = True, key: str = None, level: int = 0
) -> None:
    """Print JSON data in a tree structure with type information."""

    # Determine the connector symbol
    connector = "└─ " if is_last else "├─ "

    # Create the key-value display
    if key is not None:
        type_info = get_type_info(data)
        if isinstance(data, (dict, list)):
            print(f"{prefix}{connector}{key} ({type_info}):")
        else:
            value_str = format_value(data)
            print(f"{prefix}{connector}{key} ({type_info}): {value_str}")

    # Handle nested structures
    if isinstance(data, dict):
        # Update prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")

        items = list(data.items())
        for i, (child_key, child_value) in enumerate(items):
            is_child_last = i == len(items) - 1
            print_json_tree(
                child_value, child_prefix, is_child_last, child_key, level + 1
            )

    elif isinstance(data, list):
        # Update prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, item in enumerate(data):
            is_child_last = i == len(data) - 1
            print_json_tree(item, child_prefix, is_child_last, f"[{i}]", level + 1)


def analyze_hook_event(data: Dict[str, Any]) -> None:
    """Analyze and display hook event specific information."""
    hook_event = data.get("hook_event_name", "Unknown")

    print("\n" + "=" * 50)
    print(f"HOOK EVENT ANALYSIS: {hook_event}")
    print("=" * 50)

    if hook_event == "PreToolUse":
        tool_name = data.get("tool_name", "Unknown")
        print(f"Tool being called: {tool_name}")
        if "tool_input" in data:
            tool_input = data["tool_input"]
            if isinstance(tool_input, dict):
                print(f"Tool input parameters: {len(tool_input)} fields")

    elif hook_event == "PostToolUse":
        tool_name = data.get("tool_name", "Unknown")
        print(f"Tool completed: {tool_name}")
        if "tool_response" in data:
            tool_response = data["tool_response"]
            if isinstance(tool_response, dict):
                success = tool_response.get("success", "Unknown")
                print(f"Tool execution result: {success}")

    elif hook_event == "UserPromptSubmit":
        prompt = data.get("prompt", "")
        print(f"Prompt length: {len(prompt)} characters")

    elif hook_event in ["Stop", "SubagentStop"]:
        stop_hook_active = data.get("stop_hook_active", False)
        print(f"Stop hook already active: {stop_hook_active}")

    elif hook_event == "Notification":
        message = data.get("message", "")
        print(
            f"Notification message: {message[:100]}{'...' if len(message) > 100 else ''}"
        )

    elif hook_event == "PreCompact":
        trigger = data.get("trigger", "Unknown")
        print(f"Compact trigger: {trigger}")

    elif hook_event == "SessionStart":
        source = data.get("source", "Unknown")
        print(f"Session start source: {source}")


def main():
    """Main function to parse and display hook JSON data."""
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            print("Error: No input data received from stdin", file=sys.stderr)
            sys.exit(1)

        # Parse JSON
        try:
            # Normalize Windows paths in JSON text before parsing
            normalized_input = normalize_paths_in_json(input_data)
            data = json.loads(normalized_input)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            print(
                f"Input received: {input_data[:200]}{'...' if len(input_data) > 200 else ''}",
                file=sys.stderr,
            )
            # Also show the normalized input for debugging
            normalized_input = normalize_paths_in_json(input_data)
            print(
                f"Normalized input: {normalized_input[:200]}{'...' if len(normalized_input) > 200 else ''}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Display header
        print("=" * 60)
        print("CLAUDE CODE HOOK INPUT DATA PARSER")
        print("=" * 60)

        # Check if it's hook data by looking for common fields
        is_hook_data = any(
            key in data for key in ["session_id", "hook_event_name", "transcript_path"]
        )

        if is_hook_data:
            # Display basic hook information
            session_id = data.get("session_id", "Unknown")
            hook_event = data.get("hook_event_name", "Unknown")
            cwd = data.get("cwd", "Unknown")

            print(f"Session ID: {session_id}")
            print(f"Hook Event: {hook_event}")
            print(f"Working Directory: {cwd}")

            if "transcript_path" in data:
                print(f"Transcript Path: {data['transcript_path']}")

        # Display the full data structure
        print("\n" + "=" * 60)
        print("COMPLETE DATA STRUCTURE")
        print("=" * 60)

        if isinstance(data, dict):
            items = list(data.items())
            for i, (key, value) in enumerate(items):
                is_last = i == len(items) - 1
                print_json_tree(value, "", is_last, key)
        else:
            print_json_tree(data, "", True)

        # Hook-specific analysis
        if is_hook_data and isinstance(data, dict):
            analyze_hook_event(data)

        print("\n" + "=" * 60)

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
