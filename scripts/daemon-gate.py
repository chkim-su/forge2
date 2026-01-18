#!/usr/bin/env python3
"""
Daemon gate for workflow protocol management.

Manages workflow protocols, their phases, and validation requirements.
Works with the daemon state to track workflow progress.

Commands:
  check-protocol <workflow>      - Check if protocol exists
  get-phases <workflow>          - Get phases for workflow
  validate <workflow> <phase>    - Validate phase requirements
  list-protocols                 - List all protocols
"""

import json
import os
import sys
from pathlib import Path

# Protocol definitions
PROTOCOLS = {
    "skill_creation": {
        "phases": ["init", "intent", "semantic", "execute", "verify", "complete"],
        "required_validations": ["schema_validation"],
        "agent_required_validations": [],
        "phase_requirements": {
            "semantic": ["intent"],
            "execute": ["semantic"],
            "verify": ["execute"],
            "complete": ["verify"],
        },
    },
    "analyze_only": {
        "phases": ["init", "analysis", "complete"],
        "required_validations": [],
        "agent_required_validations": [],
        "phase_requirements": {
            "complete": ["analysis"],
        },
    },
    "verify_workflow": {
        "phases": ["init", "static_validation", "form_audit", "content_quality", "semantic_analysis", "report", "complete"],
        "required_validations": ["validate_all"],
        "agent_required_validations": ["form_selection_audit", "content_quality"],
        "phase_requirements": {
            "form_audit": ["static_validation"],
            "content_quality": ["form_audit"],
            "semantic_analysis": ["content_quality"],
            "report": ["semantic_analysis"],
            "complete": ["report"],
        },
    },
}

STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))


def ensure_state_dir():
    """Ensure state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def get_daemon_state(session_id: str = "default") -> dict:
    """Load daemon state for session."""
    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except json.JSONDecodeError:
            pass
    return {"session_id": session_id, "workflows": [], "validations": {}}


def save_daemon_state(state: dict, session_id: str = "default"):
    """Save daemon state."""
    ensure_state_dir()
    state_file = STATE_DIR / f"{session_id}.json"
    state_file.write_text(json.dumps(state, indent=2))


def check_protocol(workflow: str) -> bool:
    """Check if protocol exists."""
    return workflow in PROTOCOLS


def get_phases(workflow: str) -> list:
    """Get phases for a workflow."""
    if workflow not in PROTOCOLS:
        return []
    return PROTOCOLS[workflow]["phases"]


def get_phase_requirements(workflow: str, phase: str) -> list:
    """Get required phases before entering a phase."""
    if workflow not in PROTOCOLS:
        return []
    return PROTOCOLS[workflow].get("phase_requirements", {}).get(phase, [])


def validate_phase_entry(workflow: str, phase: str, session_id: str = "default") -> tuple:
    """
    Validate if a phase can be entered.
    Returns (allowed: bool, missing_requirements: list)
    """
    if workflow not in PROTOCOLS:
        return False, [f"Unknown workflow: {workflow}"]

    protocol = PROTOCOLS[workflow]
    if phase not in protocol["phases"]:
        return False, [f"Unknown phase: {phase} for workflow {workflow}"]

    required_phases = protocol.get("phase_requirements", {}).get(phase, [])
    if not required_phases:
        return True, []

    state = get_daemon_state(session_id)
    completed_phases = state.get("completed_phases", {}).get(workflow, [])

    missing = [p for p in required_phases if p not in completed_phases]
    return len(missing) == 0, missing


def push_workflow(session_id: str, workflow: str, initial_phase: str = "init"):
    """Push a workflow to the daemon state."""
    state = get_daemon_state(session_id)

    # Initialize workflow tracking
    if "workflows" not in state:
        state["workflows"] = []

    if "completed_phases" not in state:
        state["completed_phases"] = {}

    state["workflows"].append(workflow)
    state["current_workflow"] = workflow
    state["current_phase"] = initial_phase
    state["completed_phases"][workflow] = []

    save_daemon_state(state, session_id)
    return True


def set_workflow_phase(session_id: str, phase: str):
    """Set current workflow phase."""
    state = get_daemon_state(session_id)
    current_workflow = state.get("current_workflow")

    if not current_workflow:
        return False, "No active workflow"

    allowed, missing = validate_phase_entry(current_workflow, phase, session_id)
    if not allowed:
        return False, f"Missing requirements: {missing}"

    # Mark previous phase as completed
    prev_phase = state.get("current_phase")
    if prev_phase and prev_phase != phase:
        if current_workflow not in state["completed_phases"]:
            state["completed_phases"][current_workflow] = []
        if prev_phase not in state["completed_phases"][current_workflow]:
            state["completed_phases"][current_workflow].append(prev_phase)

    state["current_phase"] = phase
    save_daemon_state(state, session_id)
    return True, f"Phase set to {phase}"


def mark_validation(session_id: str, validation: str, status: str):
    """Mark a validation as executed/passed/failed."""
    state = get_daemon_state(session_id)

    if "validations" not in state:
        state["validations"] = {}

    state["validations"][validation] = status
    save_daemon_state(state, session_id)


def list_protocols():
    """List all available protocols."""
    for name, proto in PROTOCOLS.items():
        print(f"\n{name}:")
        print(f"  Phases: {' → '.join(proto['phases'])}")
        print(f"  Required validations: {proto['required_validations']}")
        print(f"  Agent validations: {proto['agent_required_validations']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: daemon-gate.py <command> [args...]")
        print("Commands: check-protocol, get-phases, validate, list-protocols, push-workflow, set-phase, mark-validation")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check-protocol":
        if len(sys.argv) < 3:
            print("Usage: daemon-gate.py check-protocol <workflow>", file=sys.stderr)
            sys.exit(1)
        exists = check_protocol(sys.argv[2])
        print("true" if exists else "false")
        sys.exit(0 if exists else 1)

    elif cmd == "get-phases":
        if len(sys.argv) < 3:
            print("Usage: daemon-gate.py get-phases <workflow>", file=sys.stderr)
            sys.exit(1)
        phases = get_phases(sys.argv[2])
        print(json.dumps(phases))

    elif cmd == "validate":
        if len(sys.argv) < 4:
            print("Usage: daemon-gate.py validate <workflow> <phase> [session_id]", file=sys.stderr)
            sys.exit(1)
        session_id = sys.argv[4] if len(sys.argv) > 4 else "default"
        allowed, missing = validate_phase_entry(sys.argv[2], sys.argv[3], session_id)
        if allowed:
            print("✅ Phase entry allowed")
            sys.exit(0)
        else:
            print(f"❌ Missing requirements: {missing}", file=sys.stderr)
            sys.exit(2)

    elif cmd == "list-protocols":
        list_protocols()

    elif cmd == "push-workflow":
        if len(sys.argv) < 4:
            print("Usage: daemon-gate.py push-workflow <session_id> <workflow>", file=sys.stderr)
            sys.exit(1)
        push_workflow(sys.argv[2], sys.argv[3])
        print(f"✅ Workflow {sys.argv[3]} pushed")

    elif cmd == "set-phase":
        if len(sys.argv) < 4:
            print("Usage: daemon-gate.py set-phase <session_id> <phase>", file=sys.stderr)
            sys.exit(1)
        success, msg = set_workflow_phase(sys.argv[2], sys.argv[3])
        print(msg)
        sys.exit(0 if success else 1)

    elif cmd == "mark-validation":
        if len(sys.argv) < 5:
            print("Usage: daemon-gate.py mark-validation <session_id> <validation> <status>", file=sys.stderr)
            sys.exit(1)
        mark_validation(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"✅ Validation {sys.argv[3]} marked as {sys.argv[4]}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
