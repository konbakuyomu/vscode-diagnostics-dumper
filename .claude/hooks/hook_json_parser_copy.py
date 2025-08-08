#!/usr/bin/env python3
"""
Claude Code Hook Event Name Extractor

This script extracts and prints the hook_event_name field from Claude Code hook JSON data.
Fixed encoding issues for Chinese character output in Windows environments.

Usage:
  echo '{"hook_event_name": "PreToolUse"}' | python hook_json_parser.py

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
import os
import re
import sys


def ensure_utf8_output():
    """
    Comprehensive UTF-8 setup for Windows hook environments.
    This fixes the Chinese character garbled output issue in Claude Code hooks.
    """
    if sys.platform.startswith("win"):
        # Method 1: Set environment variables for UTF-8
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "0"

        # Method 2: Try to set console code page to UTF-8
        try:
            import subprocess

            subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
        except:
            pass

        # Method 3: Force UTF-8 encoding for stdout and stderr
        import codecs

        try:
            # Reconfigure stdout and stderr to use UTF-8
            if hasattr(sys.stdout, "detach"):
                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            if hasattr(sys.stderr, "detach"):
                sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except:
            # Alternative approach if detach fails
            try:
                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
                sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
            except:
                pass


def normalize_paths_in_json(json_text: str) -> str:
    """
    Normalize Windows paths in JSON text to use forward slashes.
    This helps avoid JSON escape sequence issues with backslashes.
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


def main():
    """Extract and print the hook_event_name from JSON data."""
    # Ensure UTF-8 encoding for proper Chinese character output
    ensure_utf8_output()

    try:
        # Read JSON from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            print("Unknown", file=sys.stderr)
            sys.exit(1)

        # Parse JSON
        try:
            normalized_input = normalize_paths_in_json(input_data)
            data = json.loads(normalized_input)
        except json.JSONDecodeError:
            print("Unknown", file=sys.stderr)
            sys.exit(1)

        # Extract and print hook_event_name
        hook_event_name = data.get("hook_event_name", "Unknown")

        # Test Chinese output with proper encoding fixes
        try:
            print(f"{hook_event_name}：测试输出")
        except UnicodeEncodeError:
            # Fallback to English if encoding fails
            print(f"{hook_event_name}: Hook Test Output (Encoding Fallback)")

        # Exit normally even if "Unknown"
        sys.exit(0)

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
