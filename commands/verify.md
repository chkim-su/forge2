---
description: Verify plugin components for schema compliance
argument-hint: "[path] (default: current plugin)"
allowed-tools: ["Read", "Bash", "Grep", "Glob", "Task"]
---

# /verify Command

Validates plugin components against schemas. Invokes verify agent → you fix issues.

## Step 1: Initialize Verify Workflow

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" init verify_workflow "verify plugin"
```

## Step 2: Invoke Verify Agent

```
Task(
  subagent_type="assist-plugin:phase-verify-agent",
  prompt="Validate all components in the current plugin. Run schema_validator.py and report results.",
  description="Validate components"
)
```

## Step 3: Act on Results

Based on agent's report:

### If PASS
```
✅ Verification Complete

All components validated successfully.
```

### If FAIL
Fix the reported errors:
- Missing fields → Add to frontmatter
- Invalid format → Correct the format
- Missing registration → Add to marketplace.json

Then re-run verification:
```
Task(
  subagent_type="assist-plugin:phase-verify-agent",
  prompt="Re-validate after fixes.",
  description="Re-validate"
)
```

## Step 4: Complete

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" complete-phase
```

## Usage

```
/verify                    # Verify entire plugin
/verify skills/            # Verify skills only
/verify agents/my-agent.md # Verify specific file
```
