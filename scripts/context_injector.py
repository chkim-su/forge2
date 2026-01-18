#!/usr/bin/env python3
"""
Context injector for assist-plugin.

Loads appropriate skills based on current workflow phase.
Outputs skill loading instructions that Claude reads.
"""

import json
import sys
from pathlib import Path

STATE_FILE = Path("/tmp/assist-workflow-state.json")

# Skills to load for each phase
PHASE_SKILLS = {
    "intent": ["phase-intent"],
    "semantic": ["phase-semantic"],
    "execute": ["phase-execute"],
    "verify": ["phase-verify"]
}

# Additional skills based on component type
COMPONENT_SKILLS = {
    "SKILL": [],
    "AGENT": [],
    "COMMAND": [],
    "HOOK": [],
    "MCP": []
}


def get_state() -> dict:
    """Load current workflow state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"current_phase": "intent", "context": {}}


def inject_context():
    """Output skill loading instructions based on current phase."""
    state = get_state()
    current_phase = state.get("current_phase", "intent")
    context = state.get("context", {})
    
    # Get skills for current phase
    skills = PHASE_SKILLS.get(current_phase, [])
    
    # Add component-specific skills if determined
    component_type = context.get("component_type")
    if component_type and component_type in COMPONENT_SKILLS:
        skills.extend(COMPONENT_SKILLS[component_type])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for s in skills:
        if s not in seen:
            seen.add(s)
            unique_skills.append(s)
    
    # Output to stdout (Claude reads this)
    print(f"\n{'─' * 50}")
    print(f"📍 Assist Workflow - Phase: {current_phase.upper()}")
    print(f"{'─' * 50}")
    
    if unique_skills:
        print(f"\n🎯 Loading skills:")
        for skill in unique_skills:
            print(f'   Skill("assist-plugin:{skill}")')
    
    # Show context if available
    intent_type = context.get("intent_type")
    if intent_type:
        print(f"\n📋 Intent: {intent_type}")
    
    if component_type:
        print(f"📦 Component: {component_type}")
    
    generated = context.get("generated_files", [])
    if generated:
        print(f"📁 Generated: {len(generated)} file(s)")
    
    print(f"\n{'─' * 50}")
    
    # Phase-specific guidance
    guidance = {
        "intent": "Classify user intent: CREATE, REFACTOR, or VERIFY",
        "semantic": "Determine component type: SKILL, AGENT, COMMAND, HOOK, or MCP",
        "execute": "Generate files using appropriate schema",
        "verify": "EXIT GATE - Validate all generated components"
    }
    
    if current_phase in guidance:
        print(f"🎯 Task: {guidance[current_phase]}")
    
    print()


def main():
    inject_context()


if __name__ == "__main__":
    main()
