---
description: Comprehensive plugin verification using phase-based agent orchestration
argument-hint: "[target] (default: current plugin)"
allowed-tools: ["Read", "Bash", "Grep", "Glob", "Task"]
---

# Verify Command

Runs comprehensive verification workflow with dedicated agents per phase.

## Workflow Phases

| Phase | Agent | Purpose |
|-------|-------|---------|
| static_validation | (script) | Run schema_validator.py |
| form_audit | form-selection-auditor | Check component forms |
| content_quality | content-quality-analyzer | Check documentation |
| semantic_analysis | diagnostic-orchestrator | Deep semantic analysis |
| report | (manual) | Generate final report |

## Execution Steps

### Phase 1: Static Validation
Run the schema validator to check all component files:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validator.py"
```

### Phase 2: Form Audit
Dispatch the form-selection-auditor agent to verify component forms:
```
Task(subagent_type="forge-editor:form-selection-auditor")
```

### Phase 3: Content Quality
Dispatch the content-quality-analyzer agent:
```
Task(subagent_type="forge-editor:content-quality-analyzer")
```

### Phase 4: Semantic Analysis
Dispatch the diagnostic-orchestrator for deep analysis:
```
Task(subagent_type="forge-editor:diagnostic-orchestrator")
```

### Phase 5: Report
Generate a comprehensive verification report summarizing all findings.

## Usage

```
/verify              # Verify current plugin
/verify skills/      # Verify skills only
```

## Arguments

- `target`: Optional path to specific component or directory to verify

## Notes

- Each phase must complete successfully before proceeding to the next
- Phase transitions are tracked in the daemon state
- Agents report validation status which affects workflow progression
