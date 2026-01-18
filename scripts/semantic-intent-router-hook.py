#!/usr/bin/env python3
"""
Semantic Intent Router Hook (UserPromptSubmit)

Analyzes user intent at entry and activates appropriate workflow.
Intent analysis is NOT a separate phase - the router does it directly.

Each workflow has phases, each phase requires an agent execution before free work.

Workflows:
  - skill_creation: semantic → execute → verify (for CREATE intent)
  - verify_workflow: static_validation → form_audit → content_quality → report (for VERIFY intent)
  - refactor_workflow: analysis → plan → execute → verify (for REFACTOR intent)
"""

import json
import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
STATE_FILE = Path("/tmp/assist-workflow-state.json")
SESSION_STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))

# =============================================================================
# WORKFLOW DEFINITIONS
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
    },
    "verify_workflow": {
        # Simplified: single verify phase using existing agent
        "phases": ["verify"],
        "agents": {
            "verify": "phase-verify-agent"
        },
    },
    "refactor_workflow": {
        # Simplified: reuse existing agents
        "phases": ["semantic", "execute", "verify"],
        "agents": {
            "semantic": "phase-semantic-agent",
            "execute": "phase-execute-agent",
            "verify": "phase-verify-agent"
        },
    },
}

# Intent detection patterns
INTENT_PATTERNS = {
    "CREATE": {
        "signals": [
            r"\b(create|make|build|generate|new|add|write)\b",
            r"(만들|생성|추가|새로)",
            r"/assist\s*$",
            r"/assist\s+create",
            r"/assist\s+skill:",
            r"/assist\s+agent:",
            r"/assist\s+hook:",
            r"/assist\s+command:",
        ],
        "context_boosters": [
            r"\b(skill|agent|command|hook|mcp|component)\b",
            r"\b(plugin|feature)\b",
        ],
        "workflow": "skill_creation",
    },
    "VERIFY": {
        "signals": [
            r"\b(check|validate|verify|test|review|confirm|audit)\b",
            r"\b(correct|valid|proper|right)\b.*\?",
            r"(검증|확인|체크|테스트|검토)",
            r"/assist\s+verify",
            r"/verify",
        ],
        "context_boosters": [
            r"\b(plugin|skill|agent|component|project)\b",
            r"\b(schema|structure|format|quality)\b",
        ],
        "workflow": "verify_workflow",
    },
    "REFACTOR": {
        "signals": [
            r"\b(refactor|improve|fix|modify|update|change|enhance)\b",
            r"(수정|개선|변경|고쳐|리팩토)",
        ],
        "context_boosters": [
            r"\b(code|function|class|method|file)\b",
        ],
        "workflow": "refactor_workflow",
    },
}


def analyze_intent(user_input: str) -> dict:
    """Analyze user input and detect intent. Returns intent + workflow mapping."""
    user_input_lower = user_input.lower()
    scores = {intent: 0 for intent in INTENT_PATTERNS}

    for intent, config in INTENT_PATTERNS.items():
        # Check signals (primary patterns)
        for signal in config["signals"]:
            if re.search(signal, user_input_lower, re.IGNORECASE):
                scores[intent] += 3

        # Check context boosters
        for booster in config.get("context_boosters", []):
            if re.search(booster, user_input_lower, re.IGNORECASE):
                scores[intent] += 1

    max_score = max(scores.values())
    if max_score == 0:
        # Default to CREATE for generic /assist commands
        return {
            "intent": "CREATE",
            "confidence": 0.5,
            "workflow": "skill_creation",
        }

    winning_intent = max(scores, key=scores.get)
    config = INTENT_PATTERNS[winning_intent]

    return {
        "intent": winning_intent,
        "confidence": min(max_score / 10, 1.0),
        "workflow": config["workflow"],
    }


def initialize_workflow_state(workflow: str, intent: str, user_request: str):
    """Initialize workflow state using the new architecture."""
    workflow_def = WORKFLOWS.get(workflow, {})
    phases = workflow_def.get("phases", [])
    agents = workflow_def.get("agents", {})

    if not phases:
        return None

    first_phase = phases[0]
    first_agent = agents.get(first_phase, "unknown-agent")

    # Create state structure
    state = {
        "workflow_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().isoformat(),
        "intent": intent,
        "workflow": workflow,
        "current_phase": first_phase,
        "phase_status": "agent_required",
        "required_agent": first_agent,
        "phases": {},
        "context": {
            "user_request": user_request,
            "component_type": None,
            "component_name": None,
            "generated_files": []
        }
    }

    # Initialize phases
    for i, phase in enumerate(phases):
        state["phases"][phase] = {
            "status": "in_progress" if i == 0 else "pending",
            "agent_completed": False,
            "result": None
        }

    # Save to state file
    STATE_FILE.write_text(json.dumps(state, indent=2))

    return {
        "first_phase": first_phase,
        "first_agent": first_agent,
        "total_phases": len(phases)
    }


def save_session_state(session_id: str, workflow: str, intent: str):
    """Save workflow activation to session state for cross-session tracking."""
    SESSION_STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = SESSION_STATE_DIR / f"{session_id}.json"

    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except json.JSONDecodeError:
            pass

    # Update session state
    if "workflows" not in state:
        state["workflows"] = []
    state["workflows"].append(workflow)
    state["current_workflow"] = workflow
    state["current_intent"] = intent
    state["activated_at"] = datetime.now().isoformat()

    state_file.write_text(json.dumps(state, indent=2))


def main():
    # Read hook input from stdin (Claude Code passes JSON via stdin)
    try:
        stdin_data = sys.stdin.read()
        if stdin_data.strip():
            hook_input = json.loads(stdin_data)
            user_prompt = hook_input.get("prompt", "")
        else:
            user_prompt = ""
    except (json.JSONDecodeError, IOError):
        user_prompt = ""

    session_id = os.environ.get("SESSION_ID", "default")

    # Skip if empty prompt
    if not user_prompt.strip():
        sys.exit(0)

    # GUARD: Only process /assist commands - exit silently for other prompts
    if not user_prompt.strip().lower().startswith("/assist"):
        sys.exit(0)

    # Extract the request (remove /assist prefix)
    user_request = re.sub(r"^/assist\s*", "", user_prompt.strip(), flags=re.IGNORECASE)

    # Analyze intent directly (NOT a separate phase)
    analysis = analyze_intent(user_prompt)
    intent = analysis["intent"]
    workflow = analysis["workflow"]
    confidence = analysis["confidence"]

    # Initialize workflow state
    init_result = initialize_workflow_state(workflow, intent, user_request)
    if not init_result:
        # Unknown workflow, continue without activation
        sys.exit(0)

    # Save to session state for cross-session tracking
    save_session_state(session_id, workflow, intent)

    first_phase = init_result["first_phase"]
    first_agent = init_result["first_agent"]
    total_phases = init_result["total_phases"]

    # Output guidance in the format the user specified
    result = {
        "result": "continue",
        "additionalContext": f"""
──────────────────────────────────────────────────────
🎯 Intent: {intent} (Router analysis complete)
📋 Workflow: {workflow}
──────────────────────────────────────────────────────

📍 Phase 1/{total_phases}: {first_phase.upper()}

▶ Execute: Task("assist-plugin:{first_agent}")
──────────────────────────────────────────────────────
"""
    }

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
