#!/usr/bin/env python3
"""
Workflow phase updater for forge-editor.

Handles automatic phase transitions based on tool completion events.
Called by PostToolUse hooks to advance workflow phases.

Usage:
  workflow-phase-updater.py <event_type> [args...]

Event types:
  post_bash      - After Bash tool completes
  post_task      - After Task tool completes
  post_write     - After Write/Edit tool completes
  post_read      - After Read tool completes
"""

import json
import os
import sys
from pathlib import Path

# Phase transitions by workflow type and event
PHASE_TRANSITIONS = {
    "skill_creation": {
        "post_bash": {
            "init": "intent",
        },
        "post_task": {
            "execute": "verify",
        },
        "post_write": {
            "execute": "execute",  # Stay in execute
            "verify": "complete",
        },
    },
    "analyze_only": {
        "post_read": {
            "init": "analysis",
            "analysis": "analysis",  # Stay during analysis
        },
        "post_task": {
            "analysis": "complete",
        },
    },
    "verify_workflow": {
        "post_bash": {
            "init": "static_validation",
            "static_validation": "static_validation",  # Stay during validation
        },
        "post_task": {
            "static_validation": "form_audit",         # After validate_all -> form audit
            "form_audit": "content_quality",           # After form-selection-auditor -> content
            "content_quality": "semantic_analysis",    # After content-quality-analyzer -> semantic
            "semantic_analysis": "report",             # After diagnostic-orchestrator -> report
        },
        "post_write": {
            "report": "complete",                      # After writing report -> complete
        },
    },
}

STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))


def get_daemon_state(session_id: str = "default") -> dict:
    """Load daemon state for session."""
    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_daemon_state(state: dict, session_id: str = "default"):
    """Save daemon state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"{session_id}.json"
    state_file.write_text(json.dumps(state, indent=2))


def update_phase(event_type: str, session_id: str = "default", context: dict = None) -> tuple:
    """
    Update workflow phase based on event type.
    Returns (transitioned: bool, new_phase: str or None)
    """
    state = get_daemon_state(session_id)

    current_workflow = state.get("current_workflow")
    current_phase = state.get("current_phase")

    if not current_workflow or not current_phase:
        return False, None

    # Get transitions for this workflow
    workflow_transitions = PHASE_TRANSITIONS.get(current_workflow, {})
    event_transitions = workflow_transitions.get(event_type, {})

    # Check if current phase has a transition for this event
    new_phase = event_transitions.get(current_phase)

    if new_phase and new_phase != current_phase:
        # Mark current phase as completed
        if "completed_phases" not in state:
            state["completed_phases"] = {}
        if current_workflow not in state["completed_phases"]:
            state["completed_phases"][current_workflow] = []
        if current_phase not in state["completed_phases"][current_workflow]:
            state["completed_phases"][current_workflow].append(current_phase)

        # Update to new phase
        state["current_phase"] = new_phase
        save_daemon_state(state, session_id)
        return True, new_phase

    return False, current_phase


def check_transition_conditions(workflow: str, from_phase: str, to_phase: str, context: dict) -> bool:
    """
    Check if transition conditions are met.
    Returns True if transition is allowed.
    """
    # For verify_workflow, check validation status for certain transitions
    if workflow == "verify_workflow":
        if from_phase == "static_validation" and to_phase == "form_audit":
            # Require validate_all passed
            validations = context.get("validations", {})
            return validations.get("validate_all") == "passed"

        if from_phase == "form_audit" and to_phase == "content_quality":
            validations = context.get("validations", {})
            return validations.get("form_selection_audit") == "passed"

    return True


def get_phase_agent(workflow: str, phase: str) -> str:
    """Get the agent assigned to a phase."""
    phase_agents = {
        "verify_workflow": {
            "static_validation": None,  # Script: validate_all.py
            "form_audit": "form-selection-auditor",
            "content_quality": "content-quality-analyzer",
            "semantic_analysis": "diagnostic-orchestrator",
            "report": None,  # Manual synthesis
        },
        "skill_creation": {
            "intent": None,
            "semantic": None,
            "execute": "component-architect",
            "verify": None,
        },
    }

    return phase_agents.get(workflow, {}).get(phase)


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow-phase-updater.py <event_type> [session_id]")
        sys.exit(1)

    event_type = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("SESSION_ID", "default")

    # Get context from environment if available
    context = {}
    context_json = os.environ.get("HOOK_CONTEXT", "{}")
    try:
        context = json.loads(context_json)
    except json.JSONDecodeError:
        pass

    transitioned, new_phase = update_phase(event_type, session_id, context)

    if transitioned:
        agent = get_phase_agent(get_daemon_state(session_id).get("current_workflow", ""), new_phase)
        print(f"Phase transition: -> {new_phase}")
        if agent:
            print(f"Assigned agent: {agent}")
    else:
        state = get_daemon_state(session_id)
        print(f"Current phase: {state.get('current_phase', 'none')}")


if __name__ == "__main__":
    main()
