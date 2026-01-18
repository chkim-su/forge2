#!/usr/bin/env python3
"""
Unified workflow state management for assist-plugin.

Hook-based workflow architecture with agent-first enforcement.
Router analyzes intent at entry → each phase requires agent execution before free work.

State Commands:
  init <workflow> [phase]  - Initialize workflow state with first phase
  status                   - Show current state
  update <phase> <status>  - Update phase status
  require <phase>          - Block if prerequisite phases not complete
  set-intent <intent>      - Set intent classification
  set-component <type>     - Set component type
  add-file <filepath>      - Track a generated file
  reset                    - Reset to initial state
  complete-phase           - Mark current phase complete, transition to next
  agent-completed          - Mark agent as completed, transition to working status

Protocol Commands (merged from daemon-gate.py):
  check-protocol <workflow>        - Check if protocol exists
  get-phases <workflow>            - Get phases for workflow
  validate-phase <workflow> <phase>- Validate phase requirements
  push-workflow <workflow> [phase] - Push workflow to state
  mark-validation <name> <status>  - Mark validation result
  list-protocols                   - List all protocols
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("/tmp/assist-workflow-state.json")

# Phase order for legacy dependency checking (kept for backward compatibility)
PHASE_ORDER = ["intent", "semantic", "execute", "verify"]

# Legacy phase prerequisites (kept for backward compatibility)
PHASE_PREREQUISITES = {
    "intent": [],
    "semantic": ["intent"],
    "execute": ["intent", "semantic"],
    "verify": ["intent", "semantic", "execute"]
}

# =============================================================================
# NEW ARCHITECTURE: Workflow definitions with agent-first enforcement
# Router analyzes intent (not a phase) → each phase requires agent before free work
# =============================================================================
WORKFLOWS = {
    "skill_creation": {
        "phases": ["semantic", "execute", "verify"],
        "agents": {
            "semantic": "phase-semantic-agent",
            "execute": "phase-execute-agent",
            "verify": "phase-verify-agent"
        },
        "phase_requirements": {
            "execute": ["semantic"],
            "verify": ["execute"],
        },
    },
    "verify_workflow": {
        "phases": ["static_validation", "form_audit", "content_quality", "report"],
        "agents": {
            "static_validation": "static-validator-agent",
            "form_audit": "form-auditor-agent",
            "content_quality": "content-quality-agent",
            "report": "report-generator-agent"
        },
        "phase_requirements": {
            "form_audit": ["static_validation"],
            "content_quality": ["form_audit"],
            "report": ["content_quality"],
        },
    },
    "refactor_workflow": {
        "phases": ["analysis", "plan", "execute", "verify"],
        "agents": {
            "analysis": "refactor-analyzer-agent",
            "plan": "refactor-planner-agent",
            "execute": "refactor-executor-agent",
            "verify": "phase-verify-agent"
        },
        "phase_requirements": {
            "plan": ["analysis"],
            "execute": ["plan"],
            "verify": ["execute"],
        },
    },
}

# Legacy PROTOCOLS (kept for backward compatibility with existing scripts)
PROTOCOLS = {
    "skill_creation": {
        "phases": ["semantic", "execute", "verify"],
        "required_validations": ["schema_validation"],
        "agent_required_validations": [],
        "phase_requirements": {
            "execute": ["semantic"],
            "verify": ["execute"],
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
        "phases": ["static_validation", "form_audit", "content_quality", "report"],
        "required_validations": ["validate_all"],
        "agent_required_validations": ["form_selection_audit", "content_quality"],
        "phase_requirements": {
            "form_audit": ["static_validation"],
            "content_quality": ["form_audit"],
            "report": ["content_quality"],
        },
    },
}


def get_state() -> dict:
    """Load current state or return default."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return create_initial_state()


def create_initial_state(workflow: str = None, first_phase: str = None) -> dict:
    """Create fresh workflow state with new architecture fields."""
    state = {
        "workflow_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().isoformat(),
        # New architecture fields
        "intent": None,                    # CREATE, VERIFY, REFACTOR (set by router)
        "workflow": workflow,              # skill_creation, verify_workflow, refactor_workflow
        "current_phase": first_phase,      # Current phase in workflow
        "phase_status": "agent_required",  # agent_required | working
        "required_agent": None,            # Agent that must execute before free work
        # Phase tracking
        "phases": {},
        # Context
        "context": {
            "user_request": None,          # Original user request
            "component_type": None,        # SKILL, AGENT, COMMAND, HOOK, MCP
            "component_name": None,
            "generated_files": []
        }
    }

    # Initialize phases based on workflow
    if workflow and workflow in WORKFLOWS:
        workflow_def = WORKFLOWS[workflow]
        for phase in workflow_def["phases"]:
            state["phases"][phase] = {
                "status": "pending",
                "agent_completed": False,
                "result": None
            }
        # Set first phase and required agent
        if first_phase and first_phase in workflow_def["agents"]:
            state["required_agent"] = workflow_def["agents"][first_phase]
            state["phases"][first_phase]["status"] = "in_progress"
    else:
        # Legacy fallback
        state["current_phase"] = "intent"
        state["phases"] = {
            "intent": {"status": "pending", "result": None},
            "semantic": {"status": "pending", "result": None},
            "execute": {"status": "pending", "result": None, "files": []},
            "verify": {"status": "pending", "result": None}
        }

    return state


def save_state(state: dict):
    """Persist state to file."""
    state["updated_at"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def init_state(workflow: str = None, first_phase: str = None, intent: str = None, user_request: str = None):
    """Initialize workflow state with new architecture."""
    # Determine first phase from workflow if not specified
    if workflow and workflow in WORKFLOWS and not first_phase:
        first_phase = WORKFLOWS[workflow]["phases"][0]

    state = create_initial_state(workflow, first_phase)

    if intent:
        state["intent"] = intent.upper()
    if user_request:
        state["context"]["user_request"] = user_request

    save_state(state)

    if workflow:
        agent = state.get("required_agent", "none")
        print(f"✅ Workflow initialized: {workflow}")
        print(f"   Phase: {first_phase}")
        print(f"   Status: agent_required")
        print(f"   Required agent: {agent}")
    else:
        print(f"✅ Workflow initialized: {state['workflow_id']}")


def show_status():
    """Display current workflow state."""
    state = get_state()

    print(f"\n📊 Assist Workflow Status")
    print(f"─" * 50)

    # New architecture display
    workflow = state.get("workflow")
    if workflow:
        intent = state.get("intent", "unknown")
        phase_status = state.get("phase_status", "unknown")
        required_agent = state.get("required_agent", "none")
        current_phase = state.get("current_phase", "unknown")

        print(f"Intent: {intent}")
        print(f"Workflow: {workflow}")
        print(f"Current Phase: {current_phase}")
        print(f"Phase Status: {phase_status}")
        if phase_status == "agent_required":
            print(f"Required Agent: {required_agent}")
        print()

        # Phase status with visual indicators
        icons = {
            "pending": "○",
            "in_progress": "◐",
            "completed": "✓",
            "failed": "✗"
        }

        if workflow in WORKFLOWS:
            phases = WORKFLOWS[workflow]["phases"]
            for phase in phases:
                phase_data = state["phases"].get(phase, {})
                status = phase_data.get("status", "pending")
                agent_completed = phase_data.get("agent_completed", False)
                icon = icons.get(status, "?")

                current = " ◀" if phase == current_phase else ""
                agent_str = " [agent✓]" if agent_completed else ""

                print(f"  {icon} {phase.upper()}{agent_str}{current}")
    else:
        # Legacy display
        print(f"ID: {state.get('workflow_id', 'unknown')}")
        print(f"Current Phase: {state.get('current_phase', 'unknown')}")
        print()

        icons = {
            "pending": "○",
            "in_progress": "◐",
            "completed": "✓",
            "failed": "✗"
        }

        for phase in PHASE_ORDER:
            phase_data = state["phases"].get(phase, {})
            status = phase_data.get("status", "pending")
            result = phase_data.get("result", "")
            icon = icons.get(status, "?")

            current = " ◀" if phase == state.get("current_phase") else ""
            result_str = f" → {result}" if result else ""

            print(f"  {icon} {phase.capitalize()}{result_str}{current}")

    # Context info
    ctx = state.get("context", {})
    if ctx.get("user_request") or ctx.get("component_type"):
        print()
        print(f"Context:")
        if ctx.get("user_request"):
            req = ctx["user_request"][:50] + "..." if len(ctx.get("user_request", "")) > 50 else ctx.get("user_request")
            print(f"  Request: {req}")
        if ctx.get("component_type"):
            print(f"  Component: {ctx['component_type']}")
        if ctx.get("generated_files"):
            print(f"  Files: {len(ctx['generated_files'])} generated")


def update_phase(phase: str, status: str, result: str = None):
    """Update a phase's status."""
    if phase not in PHASE_ORDER:
        print(f"❌ Unknown phase: {phase}", file=sys.stderr)
        sys.exit(1)
    
    if status not in ["pending", "in_progress", "completed", "failed"]:
        print(f"❌ Invalid status: {status}", file=sys.stderr)
        sys.exit(1)
    
    state = get_state()
    state["phases"][phase]["status"] = status
    if result:
        state["phases"][phase]["result"] = result
    
    # Update current phase if progressing
    if status == "in_progress":
        state["current_phase"] = phase
    elif status == "completed":
        # Move to next phase
        idx = PHASE_ORDER.index(phase)
        if idx < len(PHASE_ORDER) - 1:
            state["current_phase"] = PHASE_ORDER[idx + 1]
    
    save_state(state)
    print(f"✅ Phase '{phase}' → {status}")


def require_phase(phase: str):
    """
    Block if prerequisite phases not complete.

    Exit codes:
      0 - All prerequisites met, allow
      2 - Prerequisites not met, BLOCK (stderr message shown to Claude)
    """
    state = get_state()
    prerequisites = PHASE_PREREQUISITES.get(phase, [])

    missing = []
    for prereq in prerequisites:
        prereq_status = state["phases"].get(prereq, {}).get("status", "pending")
        if prereq_status != "completed":
            missing.append(prereq)

    if missing:
        msg = f"❌ BLOCKED: Phase '{phase}' requires completion of: {', '.join(missing)}"
        print(msg, file=sys.stderr)
        sys.exit(2)  # BLOCK

    print(f"✅ Prerequisites met for '{phase}'")
    sys.exit(0)  # ALLOW


# =============================================================================
# NEW ARCHITECTURE: Phase transition functions
# =============================================================================

def agent_completed():
    """
    Mark the required agent as completed for current phase.
    Transitions phase_status from 'agent_required' to 'working'.
    Called by PostToolUse hook when the required agent finishes.
    """
    state = get_state()
    workflow = state.get("workflow")
    current_phase = state.get("current_phase")

    if not workflow:
        print("No active workflow", file=sys.stderr)
        sys.exit(1)

    # Mark agent as completed for this phase
    if current_phase in state.get("phases", {}):
        state["phases"][current_phase]["agent_completed"] = True

    # Transition to working status
    state["phase_status"] = "working"
    save_state(state)

    print(f"✅ Agent completed for phase '{current_phase}'")
    print(f"   Phase status → working (free work allowed)")


def complete_phase():
    """
    Mark current phase as complete and transition to next phase.
    The next phase starts with phase_status='agent_required'.
    """
    state = get_state()
    workflow = state.get("workflow")
    current_phase = state.get("current_phase")

    if not workflow or workflow not in WORKFLOWS:
        print(f"No active workflow or unknown workflow: {workflow}", file=sys.stderr)
        sys.exit(1)

    workflow_def = WORKFLOWS[workflow]
    phases = workflow_def["phases"]

    # Mark current phase as completed
    if current_phase in state.get("phases", {}):
        state["phases"][current_phase]["status"] = "completed"

    # Find next phase
    try:
        current_idx = phases.index(current_phase)
    except ValueError:
        print(f"Current phase '{current_phase}' not in workflow phases", file=sys.stderr)
        sys.exit(1)

    if current_idx >= len(phases) - 1:
        # Workflow complete
        state["phase_status"] = "completed"
        state["current_phase"] = None
        save_state(state)
        print(f"═" * 50)
        print(f"✅ Workflow '{workflow}' COMPLETED")
        print(f"═" * 50)
        return

    # Transition to next phase
    next_phase = phases[current_idx + 1]
    next_agent = workflow_def["agents"].get(next_phase)

    state["current_phase"] = next_phase
    state["phase_status"] = "agent_required"
    state["required_agent"] = next_agent
    state["phases"][next_phase]["status"] = "in_progress"

    save_state(state)

    print(f"─" * 50)
    print(f"✅ Phase '{current_phase}' completed")
    print(f"─" * 50)
    print()
    print(f"📍 Phase {current_idx + 2}/{len(phases)}: {next_phase.upper()}")
    print()
    print(f"▶ Execute: Task(\"forge-editor:{next_agent}\")")
    print(f"─" * 50)


def set_intent(intent_type: str):
    """Set intent classification."""
    valid_intents = ["CREATE", "REFACTOR", "VERIFY"]
    intent_upper = intent_type.upper()
    
    if intent_upper not in valid_intents:
        print(f"❌ Invalid intent: {intent_type}. Valid: {valid_intents}", file=sys.stderr)
        sys.exit(1)
    
    state = get_state()
    state["context"]["intent_type"] = intent_upper
    state["phases"]["intent"]["result"] = intent_upper
    save_state(state)
    print(f"✅ Intent set: {intent_upper}")


def set_component(component_type: str):
    """Set component type."""
    valid_types = ["SKILL", "AGENT", "COMMAND", "HOOK", "MCP"]
    type_upper = component_type.upper()
    
    if type_upper not in valid_types:
        print(f"❌ Invalid component type: {component_type}. Valid: {valid_types}", file=sys.stderr)
        sys.exit(1)
    
    state = get_state()
    state["context"]["component_type"] = type_upper
    state["phases"]["semantic"]["result"] = type_upper
    save_state(state)
    print(f"✅ Component type set: {type_upper}")


def add_generated_file(filepath: str):
    """Track a generated file."""
    state = get_state()
    if filepath not in state["context"]["generated_files"]:
        state["context"]["generated_files"].append(filepath)
        state["phases"]["execute"]["files"].append(filepath)
    save_state(state)
    print(f"✅ Tracked file: {filepath}")


def reset_state():
    """Reset workflow to initial state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    init_state()
    print("✅ Workflow reset")


# Protocol-related functions (merged from daemon-gate.py)
def check_protocol(workflow: str) -> bool:
    """Check if protocol exists."""
    return workflow in PROTOCOLS


def get_protocol_phases(workflow: str) -> list:
    """Get phases for a workflow."""
    if workflow not in PROTOCOLS:
        return []
    return PROTOCOLS[workflow]["phases"]


def get_phase_requirements(workflow: str, phase: str) -> list:
    """Get required phases before entering a phase."""
    if workflow not in PROTOCOLS:
        return []
    return PROTOCOLS[workflow].get("phase_requirements", {}).get(phase, [])


def validate_phase_entry(workflow: str, phase: str) -> tuple:
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

    state = get_state()
    # Check completed phases in state
    phases = state.get("phases", {})
    completed = [p for p, data in phases.items() if data.get("status") == "completed"]

    missing = [p for p in required_phases if p not in completed]
    return len(missing) == 0, missing


def push_workflow(workflow: str, initial_phase: str = "init"):
    """Push a workflow to the state."""
    state = get_state()
    state["current_workflow"] = workflow
    state["current_phase"] = initial_phase
    save_state(state)
    return True


def mark_validation(validation: str, status: str):
    """Mark a validation as executed/passed/failed."""
    state = get_state()
    if "validations" not in state:
        state["validations"] = {}
    state["validations"][validation] = status
    save_state(state)


def list_protocols():
    """List all available protocols."""
    for name, proto in PROTOCOLS.items():
        print(f"\n{name}:")
        print(f"  Phases: {' → '.join(proto['phases'])}")
        print(f"  Required validations: {proto['required_validations']}")
        print(f"  Agent validations: {proto['agent_required_validations']}")


def main():
    if len(sys.argv) < 2:
        show_status()
        return

    cmd = sys.argv[1].lower()

    if cmd == "init":
        # New architecture: init <workflow> [--intent=X] [--request="..."]
        workflow = sys.argv[2] if len(sys.argv) > 2 else None
        intent = None
        user_request = None
        for arg in sys.argv[3:]:
            if arg.startswith("--intent="):
                intent = arg.split("=", 1)[1]
            elif arg.startswith("--request="):
                user_request = arg.split("=", 1)[1]
        init_state(workflow=workflow, intent=intent, user_request=user_request)
    elif cmd == "status":
        show_status()
    elif cmd == "update":
        if len(sys.argv) < 4:
            print("Usage: workflow_state.py update <phase> <status> [result]", file=sys.stderr)
            sys.exit(1)
        result = sys.argv[4] if len(sys.argv) > 4 else None
        update_phase(sys.argv[2], sys.argv[3], result)
    # New architecture commands
    elif cmd == "complete-phase":
        complete_phase()
    elif cmd == "agent-completed":
        agent_completed()
    elif cmd == "require":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py require <phase>", file=sys.stderr)
            sys.exit(1)
        require_phase(sys.argv[2])
    elif cmd == "set-intent":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py set-intent <CREATE|REFACTOR|VERIFY>", file=sys.stderr)
            sys.exit(1)
        set_intent(sys.argv[2])
    elif cmd == "set-component":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py set-component <SKILL|AGENT|COMMAND|HOOK|MCP>", file=sys.stderr)
            sys.exit(1)
        set_component(sys.argv[2])
    elif cmd == "add-file":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py add-file <filepath>", file=sys.stderr)
            sys.exit(1)
        add_generated_file(sys.argv[2])
    elif cmd == "reset":
        reset_state()
    # Protocol-related commands (merged from daemon-gate.py)
    elif cmd == "check-protocol":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py check-protocol <workflow>", file=sys.stderr)
            sys.exit(1)
        exists = check_protocol(sys.argv[2])
        print("true" if exists else "false")
        sys.exit(0 if exists else 1)
    elif cmd == "get-phases":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py get-phases <workflow>", file=sys.stderr)
            sys.exit(1)
        import json as json_mod
        phases = get_protocol_phases(sys.argv[2])
        print(json_mod.dumps(phases))
    elif cmd == "validate-phase":
        if len(sys.argv) < 4:
            print("Usage: workflow_state.py validate-phase <workflow> <phase>", file=sys.stderr)
            sys.exit(1)
        allowed, missing = validate_phase_entry(sys.argv[2], sys.argv[3])
        if allowed:
            print("✅ Phase entry allowed")
            sys.exit(0)
        else:
            print(f"❌ Missing requirements: {missing}", file=sys.stderr)
            sys.exit(2)
    elif cmd == "push-workflow":
        if len(sys.argv) < 3:
            print("Usage: workflow_state.py push-workflow <workflow> [initial_phase]", file=sys.stderr)
            sys.exit(1)
        initial = sys.argv[3] if len(sys.argv) > 3 else "init"
        push_workflow(sys.argv[2], initial)
        print(f"✅ Workflow {sys.argv[2]} pushed")
    elif cmd == "mark-validation":
        if len(sys.argv) < 4:
            print("Usage: workflow_state.py mark-validation <validation> <status>", file=sys.stderr)
            sys.exit(1)
        mark_validation(sys.argv[2], sys.argv[3])
        print(f"✅ Validation {sys.argv[2]} marked as {sys.argv[3]}")
    elif cmd == "list-protocols":
        list_protocols()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Commands: init, status, update, require, set-intent, set-component, add-file, reset")
        print("Protocol commands: check-protocol, get-phases, validate-phase, push-workflow, mark-validation, list-protocols")
        sys.exit(1)


if __name__ == "__main__":
    main()
