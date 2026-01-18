#!/usr/bin/env python3
"""
Workflow state management for assist-plugin.

Tracks the 4-phase workflow: intent → semantic → execute → verify

Commands:
  init                     - Initialize workflow state
  status                   - Show current state
  update <phase> <status>  - Update phase status
  require <phase>          - Block if prerequisite phases not complete
  set-intent <intent>      - Set intent classification
  set-component <type>     - Set component type
  reset                    - Reset to initial state
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("/tmp/assist-workflow-state.json")

# Phase order for dependency checking
PHASE_ORDER = ["intent", "semantic", "execute", "verify"]

# Phase prerequisites
PHASE_PREREQUISITES = {
    "intent": [],
    "semantic": ["intent"],
    "execute": ["intent", "semantic"],
    "verify": ["intent", "semantic", "execute"]
}


def get_state() -> dict:
    """Load current state or return default."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return create_initial_state()


def create_initial_state() -> dict:
    """Create fresh workflow state."""
    return {
        "workflow_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().isoformat(),
        "current_phase": "intent",
        "phases": {
            "intent": {"status": "pending", "result": None},
            "semantic": {"status": "pending", "result": None},
            "execute": {"status": "pending", "result": None, "files": []},
            "verify": {"status": "pending", "result": None}
        },
        "context": {
            "intent_type": None,      # CREATE, REFACTOR, VERIFY
            "component_type": None,    # SKILL, AGENT, COMMAND, HOOK, MCP
            "component_name": None,
            "generated_files": []
        }
    }


def save_state(state: dict):
    """Persist state to file."""
    state["updated_at"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def init_state():
    """Initialize or reset workflow state."""
    state = create_initial_state()
    save_state(state)
    print(f"✅ Workflow initialized: {state['workflow_id']}")


def show_status():
    """Display current workflow state."""
    state = get_state()
    
    print(f"\n📊 Assist Workflow Status")
    print(f"─" * 40)
    print(f"ID: {state.get('workflow_id', 'unknown')}")
    print(f"Current Phase: {state['current_phase']}")
    print()
    
    # Phase status with visual indicators
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
        
        current = " ◀" if phase == state["current_phase"] else ""
        result_str = f" → {result}" if result else ""
        
        print(f"  {icon} {phase.capitalize()}{result_str}{current}")
    
    # Context info
    ctx = state.get("context", {})
    if ctx.get("intent_type") or ctx.get("component_type"):
        print()
        print(f"Context:")
        if ctx.get("intent_type"):
            print(f"  Intent: {ctx['intent_type']}")
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


def main():
    if len(sys.argv) < 2:
        show_status()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "init":
        init_state()
    elif cmd == "status":
        show_status()
    elif cmd == "update":
        if len(sys.argv) < 4:
            print("Usage: workflow_state.py update <phase> <status> [result]", file=sys.stderr)
            sys.exit(1)
        result = sys.argv[4] if len(sys.argv) > 4 else None
        update_phase(sys.argv[2], sys.argv[3], result)
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
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Commands: init, status, update, require, set-intent, set-component, add-file, reset")
        sys.exit(1)


if __name__ == "__main__":
    main()
