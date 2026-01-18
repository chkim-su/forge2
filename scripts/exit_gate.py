#!/usr/bin/env python3
"""
Exit gate for assist-plugin workflow.

Enforces mandatory verification before workflow completion.
Runs on Stop event to ensure all generated components are valid.

Exit codes:
  0 - Verification passed
  2 - Verification failed (shows errors to Claude)
"""

import json
import os
import sys
from pathlib import Path

STATE_FILE = Path("/tmp/assist-workflow-state.json")
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))


def get_state() -> dict:
    """Load current workflow state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def check_workflow_progress(state: dict) -> list:
    """Check if workflow has made progress worth validating."""
    errors = []

    phases = state.get("phases", {})
    context = state.get("context", {})
    workflow_type = state.get("workflow_type", "skill_creation")

    # Get the final phase for this workflow
    phase_list = list(phases.keys())
    final_phase = phase_list[-1] if phase_list else "verify"

    # Check if any work was done
    generated_files = context.get("generated_files", [])
    has_execute = "execute" in phases
    execute_completed = phases.get("execute", {}).get("status") == "completed"

    if (has_execute and execute_completed) or generated_files:
        # Work was done, final phase (verify) is required
        final_status = phases.get(final_phase, {}).get("status", "pending")
        if final_status != "completed":
            errors.append(f"⚠️  Work completed but {final_phase} phase not run")

    return errors


def run_schema_validation() -> tuple:
    """Run schema validator on all components."""
    import subprocess
    
    validator_path = PLUGIN_ROOT / "scripts" / "schema_validator.py"
    if not validator_path.exists():
        return False, ["Schema validator not found"]
    
    result = subprocess.run(
        [sys.executable, str(validator_path), "--quiet"],
        capture_output=True,
        text=True
    )
    
    errors = []
    if result.returncode != 0:
        if result.stderr:
            errors.extend(result.stderr.strip().split("\n"))
    
    return result.returncode == 0, errors


def update_final_phase(success: bool):
    """Update final phase status in workflow state."""
    state = get_state()
    if not state:
        return

    phases = state.get("phases", {})
    if not phases:
        return

    # Get the final phase for this workflow
    phase_list = list(phases.keys())
    final_phase = phase_list[-1] if phase_list else None

    if final_phase and final_phase in phases:
        phases[final_phase]["status"] = "completed" if success else "failed"
        phases[final_phase]["result"] = "PASSED" if success else "FAILED"
        STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = get_state()
    
    # Check if this is an assist workflow
    if not state:
        # No workflow state, skip validation
        sys.exit(0)
    
    workflow_id = state.get("workflow_id")
    if not workflow_id:
        # Not an assist workflow
        sys.exit(0)
    
    all_errors = []
    
    # Check workflow progress
    progress_errors = check_workflow_progress(state)
    all_errors.extend(progress_errors)
    
    # Run schema validation
    valid, validation_errors = run_schema_validation()
    all_errors.extend(validation_errors)
    
    if all_errors:
        print("\n" + "═" * 50, file=sys.stderr)
        print("❌ EXIT GATE - Verification Required", file=sys.stderr)
        print("═" * 50, file=sys.stderr)
        
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        
        print("\n📋 Required actions:", file=sys.stderr)
        print("  1. Fix the errors listed above", file=sys.stderr)
        print("  2. Run: Skill(\"assist-plugin:phase-verify\")", file=sys.stderr)
        print("  3. Confirm all validations pass", file=sys.stderr)
        print("═" * 50, file=sys.stderr)
        
        update_final_phase(False)
        sys.exit(2)  # BLOCK
    
    # All good
    print("\n" + "═" * 50)
    print("✅ EXIT GATE - Verification Passed")
    print("═" * 50)
    
    generated = state.get("context", {}).get("generated_files", [])
    if generated:
        print(f"\n📁 Generated files ({len(generated)}):")
        for f in generated:
            print(f"   {f}")
    
    print("\n🎉 Workflow completed successfully!")
    print("═" * 50)
    
    update_final_phase(True)
    sys.exit(0)


if __name__ == "__main__":
    main()
