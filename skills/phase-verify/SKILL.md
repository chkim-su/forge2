---
name: phase-verify
description: Phase 4 of assist workflow - EXIT GATE validation. Schema compliance check before completion.
allowed-tools: ["Read", "Bash", "Grep"]
---

# Phase 4: Verify (EXIT GATE)

**MANDATORY** - This phase cannot be skipped. All generated components must pass validation.

## Purpose

Ensure generated components are:
1. Schema-compliant (frontmatter, structure)
2. Properly registered (marketplace.json)
3. Internally consistent (references exist, scripts work)

## Validation Script

```bash
python3 scripts/schema_validator.py \
  --path {generated_path} \
  --type {skill|agent|command|hook} \
  --strict
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | ✅ PASS | Workflow complete |
| 2 | ❌ FAIL | Show errors, require fix |

## Validation Checklist

### All Components

- [ ] File exists at expected path
- [ ] Frontmatter is valid YAML
- [ ] Required fields present
- [ ] Field values match schema types

### Skill-Specific

- [ ] SKILL.md exists in directory
- [ ] `name` matches directory name
- [ ] `description` is non-empty
- [ ] `allowed-tools` is valid array (if present)
- [ ] Word count < 500 (warning if exceeded)
- [ ] Referenced files in `references/` exist

### Agent-Specific

- [ ] File ends with `.md`
- [ ] `name` and `description` present
- [ ] `tools` field valid (array, omitted, or empty)
- [ ] `skills` reference existing skills
- [ ] `model` is valid (opus/sonnet/haiku)

### Command-Specific

- [ ] File ends with `.md`
- [ ] `description` present
- [ ] `argument-hint` format valid

### Hook-Specific

- [ ] Valid JSON syntax
- [ ] Event types are known
- [ ] Matcher patterns are valid regex
- [ ] Referenced scripts exist
- [ ] Timeout values reasonable (3-60s)

## Error Categories

### E0XX - Blocking Errors

Must be fixed before proceeding:

```
E001: Missing required file
E002: Invalid YAML frontmatter
E003: Missing required field
E004: Type mismatch
E005: Referenced file not found
```

### W0XX - Warnings

Allowed to proceed, but should address:

```
W001: SKILL.md exceeds 500 words
W002: No description triggers
W003: tools: [] but description implies tool usage
W004: Unregistered in marketplace.json
```

## Auto-Fix Options

```bash
# Preview fixes without applying
python3 scripts/schema_validator.py --fix --dry-run

# Apply fixes automatically
python3 scripts/schema_validator.py --fix
```

### Auto-Fixable Issues

| Issue | Auto-Fix |
|-------|----------|
| Missing marketplace.json entry | Add entry |
| Frontmatter formatting | Reformat YAML |
| Missing references directory | Create directory |

### Manual Fix Required

| Issue | Why |
|-------|-----|
| Missing required fields | Need user input |
| Invalid field values | Need clarification |
| Wrong component type | Design decision |

## Output Format

```yaml
Phase: verify
Status: completed  # or failed
Result:
  passed: true
  errors: []
  warnings:
    - W001: SKILL.md is 523 words (recommended < 500)
  auto_fixed:
    - Added skill to marketplace.json
```

## State Update

```bash
# On success
python3 scripts/workflow_state.py update verify completed

# On failure
python3 scripts/workflow_state.py update verify failed
```

## Integration with Hooks

The verify phase is enforced via Stop hook:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/schema_validator.py\" --strict",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

## Retry on Failure

If validation fails:

1. Show specific error messages
2. Suggest fixes (or apply auto-fix)
3. Re-run verification
4. Loop until pass or user abort

```
┌────────────────────────────────────────┐
│  ❌ Verification Failed                │
│                                        │
│  E003: Missing 'description' field     │
│        in agents/my-agent.md           │
│                                        │
│  Fix: Add description to frontmatter   │
│                                        │
│  Options:                              │
│  1. Fix manually and re-verify         │
│  2. [Auto-fix] Add placeholder         │
│  3. Abort workflow                     │
└────────────────────────────────────────┘
```

## Completion

When all validations pass:

```
┌────────────────────────────────────────┐
│  ✅ Verification Complete              │
│                                        │
│  Generated:                            │
│  • skills/my-skill/SKILL.md            │
│  • skills/my-skill/references/guide.md │
│                                        │
│  Registered in marketplace.json ✓      │
│  Schema validation passed ✓            │
│                                        │
│  Workflow Status: SUCCESS              │
└────────────────────────────────────────┘
```
