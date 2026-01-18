#!/usr/bin/env python3
"""
Task PostToolUse router for forge-editor.

Detects which agent completed and marks appropriate validations.
Called after Task tool completes to track agent execution.

Reads tool input/output from environment variables provided by hooks.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))

# Patterns that indicate a successful pass
PASS_PATTERNS = [
    "pass",
    "passed",
    "success",
    "successful",
    "valid",
    "validated",
    "complete",
    "completed",
    "no issues",
    "no errors",
    "all checks pass",
    "all validations pass",
]


def run_forge_state(cmd: str, *args):
    """Run forge state command."""
    daemon_gate = PLUGIN_ROOT / "scripts" / "daemon-gate.py"
    if daemon_gate.exists():
        subprocess.run(
            [sys.executable, str(daemon_gate), cmd, *args],
            capture_output=True
        )


def check_pass_patterns(output: str) -> bool:
    """Check if output indicates a pass."""
    output_lower = output.lower()
    for pattern in PASS_PATTERNS:
        if pattern in output_lower:
            return True
    return False


def detect_agent_and_mark_validation(input_str: str, tool_output: str, session_id: str):
    """
    Detect which agent was called and mark appropriate validations.
    """
    input_lower = input_str.lower()

    # Pattern: form-selection-auditor (verify workflow)
    if "form-selection-auditor" in input_lower:
        run_forge_state("mark-validation", session_id, "form_selection_audit", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "form_selection_audit", "passed")
        return "form-selection-auditor"

    # Pattern: content-quality-analyzer (verify workflow)
    if "content-quality-analyzer" in input_lower or "content-quality" in input_lower:
        run_forge_state("mark-validation", session_id, "content_quality", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "content_quality", "passed")
        return "content-quality-analyzer"

    # Pattern: diagnostic-orchestrator (verify workflow)
    if "diagnostic-orchestrator" in input_lower:
        run_forge_state("mark-validation", session_id, "semantic_analysis", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "semantic_analysis", "passed")
        return "diagnostic-orchestrator"

    # Pattern: component-architect (skill_creation workflow)
    if "component-architect" in input_lower:
        run_forge_state("mark-validation", session_id, "component_generation", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "component_generation", "passed")
        return "component-architect"

    # Pattern: plugin-validator (validation agent)
    if "plugin-validator" in input_lower:
        run_forge_state("mark-validation", session_id, "plugin_validation", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "plugin_validation", "passed")
        return "plugin-validator"

    # Pattern: skill-reviewer
    if "skill-reviewer" in input_lower:
        run_forge_state("mark-validation", session_id, "skill_review", "executed")
        if check_pass_patterns(tool_output):
            run_forge_state("mark-validation", session_id, "skill_review", "passed")
        return "skill-reviewer"

    return None


def trigger_phase_update(session_id: str):
    """Trigger workflow phase update after Task completion."""
    phase_updater = PLUGIN_ROOT / "scripts" / "workflow-phase-updater.py"
    if phase_updater.exists():
        result = subprocess.run(
            [sys.executable, str(phase_updater), "post_task", session_id],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout.strip())


def main():
    # Get tool input and output from environment
    tool_input = os.environ.get("TOOL_INPUT", "{}")
    tool_output = os.environ.get("TOOL_OUTPUT", "")
    session_id = os.environ.get("SESSION_ID", "default")

    # Parse tool input
    try:
        input_data = json.loads(tool_input)
        if isinstance(input_data, dict):
            input_str = json.dumps(input_data)
        else:
            input_str = str(input_data)
    except json.JSONDecodeError:
        input_str = tool_input

    # Detect agent and mark validation
    detected_agent = detect_agent_and_mark_validation(input_str, tool_output, session_id)

    if detected_agent:
        print(f"Detected agent: {detected_agent}")

        # Trigger phase update
        trigger_phase_update(session_id)

        # Output result for hooks
        result = {
            "result": "continue",
            "additionalContext": f"Agent `{detected_agent}` completed. Phase may have advanced."
        }
        print(json.dumps(result))
    else:
        # No specific agent detected, still trigger phase update
        trigger_phase_update(session_id)


if __name__ == "__main__":
    main()
