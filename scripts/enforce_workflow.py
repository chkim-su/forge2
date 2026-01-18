#!/usr/bin/env python3
"""
PreToolUse hook: Enforce agent-first workflow execution.

When phase_status is "agent_required":
  - ALLOW: Task tool with the required agent
  - BLOCK: All other tools

When phase_status is "working":
  - ALLOW: All tools

Exit codes:
  0 - Allow tool execution
  2 - Block tool execution (stderr message shown to Claude)
"""

import json
import sys
import os
from pathlib import Path

STATE_FILE = Path("/tmp/assist-workflow-state.json")


def get_state() -> dict:
    """Load current workflow state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def main():
    state = get_state()

    # No active workflow → allow all tools
    workflow = state.get("workflow")
    if not workflow:
        sys.exit(0)  # ALLOW

    phase_status = state.get("phase_status", "")
    required_agent = state.get("required_agent", "")
    current_phase = state.get("current_phase", "")

    # Get tool info from environment (set by Claude Code hooks)
    tool_name = os.environ.get("TOOL_NAME", "")
    tool_input = os.environ.get("TOOL_INPUT", "{}")

    # If workflow is completed, allow all
    if phase_status == "completed":
        sys.exit(0)  # ALLOW

    # Agent required phase: only allow Task with correct agent
    if phase_status == "agent_required":
        if tool_name == "Task":
            try:
                input_data = json.loads(tool_input)
                called_agent = input_data.get("subagent_type", "")

                # Allow if the required agent is being called
                if required_agent and required_agent in called_agent:
                    sys.exit(0)  # ALLOW

                # Also allow if the full plugin:agent format matches
                if f"assist-plugin:{required_agent}" in called_agent:
                    sys.exit(0)  # ALLOW
            except json.JSONDecodeError:
                pass

        # Block everything else with helpful message
        print(f"─" * 50, file=sys.stderr)
        print(f"❌ BLOCKED: Phase requires agent execution first", file=sys.stderr)
        print(f"─" * 50, file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"📍 Current Phase: {current_phase.upper()}", file=sys.stderr)
        print(f"   Phase Status: agent_required", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"▶ Execute: Task(\"assist-plugin:{required_agent}\")", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"─" * 50, file=sys.stderr)
        sys.exit(2)  # BLOCK

    # Working phase: allow all tools
    elif phase_status == "working":
        sys.exit(0)  # ALLOW

    # Unknown status: allow (fail open for safety)
    else:
        sys.exit(0)  # ALLOW


if __name__ == "__main__":
    main()
