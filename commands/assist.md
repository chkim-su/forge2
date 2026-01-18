---
description: Create Claude Code components (skill, agent, command, hook, MCP) with phase-aware guidance
argument-hint: "[component description or 'help']"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Skill", "Task", "AskUserQuestion"]
---

# /assist Command - Orchestration Instructions

Execute the phase-based workflow. Each phase: **Agent analyzes → You act on analysis**.

## Workflow Pattern

```
For each phase:
  1. Invoke agent → Agent returns analysis/info
  2. You (main LLM) do actual work based on agent output
  3. Complete phase → Move to next
```

## Step 1: Read Workflow State

```bash
cat /tmp/assist-workflow-state.json
```

Get: `workflow`, `current_phase`, `required_agent`, `context.user_request`

## Step 2: Execute Phase Loop

### Phase: SEMANTIC

**Agent task:** Classify component type

```
Task(
  subagent_type="assist-plugin:phase-semantic-agent",
  prompt="Classify component type for: {user_request}. Return: component_type, reasoning.",
  description="Classify component"
)
```

**You do:** Update workflow state with component type:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" set-component {SKILL|AGENT|COMMAND|HOOK|MCP}
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" complete-phase
```

---

### Phase: EXECUTE

**Agent task:** Plan file structure and content

```
Task(
  subagent_type="assist-plugin:phase-execute-agent",
  prompt="Plan component structure for {component_type}. Return: file paths, frontmatter fields, content outline.",
  description="Plan component"
)
```

**You do:** Actually create the files based on agent's plan:
- Write SKILL.md / agent.md / command.md / hook config
- Use proper frontmatter from schema
- Register in marketplace.json

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" add-file "path/to/file"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" complete-phase
```

---

### Phase: VERIFY

**Agent task:** Validate generated components

```
Task(
  subagent_type="assist-plugin:phase-verify-agent",
  prompt="Validate files in workflow state. Run schema_validator.py. Return: pass/fail, errors, warnings.",
  description="Validate components"
)
```

**You do:**
- If PASS: Report success, complete workflow
- If FAIL: Fix errors based on agent feedback, re-verify

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" complete-phase
```

## Step 3: Report Completion

```
✅ Workflow Complete

Created: {component_type}
Files:
• path/to/file1
• path/to/file2

Validation: PASSED
```

## Workflow Definitions

| Workflow | Phases |
|----------|--------|
| skill_creation | semantic → execute → verify |
| verify_workflow | verify |
| refactor_workflow | semantic → execute → verify |

## If State Missing

Ask user what they want to create, then initialize manually:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py" init skill_creation "user request"
```

## Key Rules

1. **Agent = analysis/info provider** (classification, validation, planning)
2. **You = executor** (file writes, edits, registration)
3. Always invoke agent FIRST at each phase
4. Use agent's output to guide your actions
5. Complete phase before moving to next
