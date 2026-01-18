#!/usr/bin/env python3
"""
Task PostToolUse router for forge-editor.

NEW ARCHITECTURE:
- Detects when the required agent completes
- Transitions phase_status from 'agent_required' to 'working'
- Outputs guidance for free work phase

LEGACY:
- Still marks validations for backward compatibility

Reads tool input/output from environment variables provided by hooks.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
STATE_FILE = Path("/tmp/assist-workflow-state.json")
SESSION_STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))


def get_workflow_state() -> dict:
    """Load current workflow state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def run_workflow_state_cmd(cmd: str):
    """Run workflow_state.py command."""
    workflow_state = PLUGIN_ROOT / "scripts" / "workflow_state.py"
    if workflow_state.exists():
        result = subprocess.run(
            [sys.executable, str(workflow_state), cmd],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout.strip())
        return result.returncode
    return 1


def detect_called_agent(tool_input: str) -> str:
    """Extract the agent name from Task tool input."""
    try:
        input_data = json.loads(tool_input)
        subagent_type = input_data.get("subagent_type", "")
        # Extract agent name (may be in format "plugin:agent" or just "agent")
        if ":" in subagent_type:
            return subagent_type.split(":")[-1]
        return subagent_type
    except json.JSONDecodeError:
        # Try to find agent name in the string
        input_lower = tool_input.lower()
        # Check for phase agents
        phase_agents = [
            "phase-semantic-agent",
            "phase-execute-agent",
            "phase-verify-agent",
            "static-validator-agent",
            "form-auditor-agent",
            "content-quality-agent",
            "report-generator-agent",
            "refactor-analyzer-agent",
            "refactor-planner-agent",
            "refactor-executor-agent",
            "component-architect",
        ]
        for agent in phase_agents:
            if agent in input_lower:
                return agent
    return ""


def main():
    # Get tool input and output from environment
    tool_input = os.environ.get("TOOL_INPUT", "{}")
    tool_output = os.environ.get("TOOL_OUTPUT", "")
    session_id = os.environ.get("SESSION_ID", "default")

    # Load current workflow state
    state = get_workflow_state()
    workflow = state.get("workflow")
    phase_status = state.get("phase_status", "")
    required_agent = state.get("required_agent", "")
    current_phase = state.get("current_phase", "")

    # Detect which agent was called
    called_agent = detect_called_agent(tool_input)

    # NEW ARCHITECTURE: Check if this is the required agent
    if workflow and phase_status == "agent_required" and required_agent:
        # Check if the called agent matches the required agent
        if called_agent and (required_agent in called_agent or called_agent in required_agent):
            # Call workflow_state.py agent-completed
            run_workflow_state_cmd("agent-completed")

            # Output guidance for free work phase
            result = {
                "result": "continue",
                "additionalContext": f"""
──────────────────────────────────────────────────────
✅ {called_agent} completed
──────────────────────────────────────────────────────

Free work is now allowed.
When this phase is complete, say "phase complete" or run:
  workflow_state.py complete-phase
──────────────────────────────────────────────────────
"""
            }
            print(json.dumps(result))
            return

    # LEGACY: For backward compatibility, still detect agents for validation marking
    # This handles cases where validation tracking is needed
    input_lower = tool_input.lower()

    # Pattern detection for legacy validation marking
    if "form-selection-auditor" in input_lower:
        print("Detected legacy agent: form-selection-auditor")
    elif "content-quality-analyzer" in input_lower or "content-quality" in input_lower:
        print("Detected legacy agent: content-quality-analyzer")
    elif "diagnostic-orchestrator" in input_lower:
        print("Detected legacy agent: diagnostic-orchestrator")
    elif "component-architect" in input_lower:
        print("Detected legacy agent: component-architect")
    elif called_agent:
        print(f"Agent completed: {called_agent}")


if __name__ == "__main__":
    main()
