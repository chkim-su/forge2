#!/usr/bin/env python3
"""
Semantic Intent Router Hook (UserPromptSubmit)

Analyzes user intent semantically and activates appropriate workflow.
Each workflow has phases, each phase has an assigned agent.

This hook runs on every user prompt to detect intent and activate workflows.
"""

import json
import os
import sys
import re
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
STATE_DIR = Path(os.path.expanduser("~/.claude/forge-state"))

# Semantic intent patterns (signals + context, not exact keywords)
INTENT_WORKFLOWS = {
    "VERIFY": {
        "signals": [
            r"\b(check|validate|verify|test|review|confirm|audit)\b",
            r"\b(correct|valid|proper|right)\b.*\?",
            r"\b(is|does|are)\b.*\b(this|it|my)\b.*\?",
            r"(맞|검증|확인|체크|테스트|검토)",
            r"/assist\s+verify",
            r"/verify",
        ],
        "context_boosters": [
            r"\b(plugin|skill|agent|component|project)\b",
            r"\b(schema|structure|format|quality)\b",
        ],
        "workflow": "verify_workflow",
        "initial_phase": "static_validation",
        "phase_agents": {
            "static_validation": None,  # Script: validate_all.py
            "form_audit": "form-selection-auditor",
            "content_quality": "content-quality-analyzer",
            "semantic_analysis": "diagnostic-orchestrator",
            "report": None,  # Synthesis
        },
    },
    "CREATE": {
        "signals": [
            r"\b(create|make|build|generate|new|add|write)\b",
            r"(만들|생성|추가|새로)",
            r"/assist\s*$",
            r"/assist\s+create",
        ],
        "context_boosters": [
            r"\b(skill|agent|command|hook|mcp|component)\b",
            r"\b(plugin|feature)\b",
        ],
        "workflow": "skill_creation",
        "initial_phase": "intent",
        "phase_agents": {
            "intent": None,
            "semantic": None,
            "execute": "component-architect",
            "verify": None,
        },
    },
    "ANALYZE": {
        "signals": [
            r"\b(analyze|understand|explain|what|how|why|show|describe)\b",
            r"(분석|이해|설명|뭐|어떻게)",
        ],
        "context_boosters": [
            r"\b(code|file|function|class|structure)\b",
        ],
        "workflow": "analyze_only",
        "initial_phase": "init",
        "phase_agents": {},
    },
}


def analyze_semantic_intent(user_input: str) -> dict:
    """Analyze user input and return intent + workflow mapping."""
    user_input_lower = user_input.lower()
    scores = {intent: 0 for intent in INTENT_WORKFLOWS}

    for intent, config in INTENT_WORKFLOWS.items():
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
        return None

    winning_intent = max(scores, key=scores.get)
    config = INTENT_WORKFLOWS[winning_intent]

    return {
        "intent": winning_intent,
        "confidence": min(max_score / 10, 1.0),
        "workflow": config["workflow"],
        "initial_phase": config["initial_phase"],
        "phase_agents": config.get("phase_agents", {}),
    }


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


def activate_workflow(session_id: str, workflow: str, phase: str, phase_agents: dict):
    """Push workflow to daemon state and set initial phase."""
    state = get_daemon_state(session_id)

    # Initialize workflow tracking
    if "workflows" not in state:
        state["workflows"] = []

    if "completed_phases" not in state:
        state["completed_phases"] = {}

    if "validations" not in state:
        state["validations"] = {}

    state["workflows"].append(workflow)
    state["current_workflow"] = workflow
    state["current_phase"] = phase
    state["phase_agents"] = phase_agents
    state["completed_phases"][workflow] = []

    save_daemon_state(state, session_id)
    return True


def get_phase_instruction(phase: str, phase_agents: dict) -> str:
    """Get instruction for current phase."""
    agent = phase_agents.get(phase)

    if phase == "static_validation":
        return "Run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/schema_validator.py`"
    elif agent:
        return f"Dispatch: `Task(subagent_type=\"forge-editor:{agent}\")`"
    else:
        return "Complete this phase manually"


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
    if not user_prompt.strip().startswith("/assist"):
        sys.exit(0)

    # Analyze intent
    analysis = analyze_semantic_intent(user_prompt)
    if not analysis:
        # No clear intent, continue normal flow
        sys.exit(0)

    # Activate workflow
    activate_workflow(
        session_id,
        analysis["workflow"],
        analysis["initial_phase"],
        analysis.get("phase_agents", {})
    )

    # Generate phase -> agent guidance
    phase_agents = analysis.get("phase_agents", {})
    phase_guide_lines = []
    for phase, agent in phase_agents.items():
        agent_name = agent if agent else "(script)"
        phase_guide_lines.append(f"  - {phase}: {agent_name}")
    phase_guide = "\n".join(phase_guide_lines) if phase_guide_lines else "  (no phase agents defined)"

    # Get instruction for initial phase
    initial_instruction = get_phase_instruction(analysis["initial_phase"], phase_agents)

    result = {
        "result": "continue",
        "additionalContext": f"""
## Semantic Intent Detected

**Intent:** {analysis["intent"]} (confidence: {analysis["confidence"]:.0%})
**Workflow Activated:** {analysis["workflow"]}
**Current Phase:** {analysis["initial_phase"]}

### Phase -> Agent Mapping
{phase_guide}

### Next Action
For phase `{analysis["initial_phase"]}`:
{initial_instruction}
"""
    }

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
