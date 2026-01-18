# Command Schema Reference

## File Structure

```
commands/{command-name}.md    # Single file with frontmatter + body
```

## Frontmatter (REQUIRED)

```yaml
---
description: "What this command does"
argument-hint: "[options]"
allowed-tools: ["Read", "Write", "Bash"]
---
```

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `description` | ✅ | string | Shown in `/help` command list |
| `argument-hint` | ❌ | string | Usage hint shown after command name |
| `allowed-tools` | ❌ | array | Restrict available tools |

## Body Structure

```markdown
# /{command-name} Command

[Overview: what this command does for the user]

## Usage

```
/{command-name} {example-usage}
/{command-name} {another-example}
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `{arg1}` | Yes/No | What it does |

## Workflow

[Step-by-step what happens when command runs]

## Examples

### Example 1: {Scenario}

```
/{command-name} {specific-example}
```

Result: {what happens}

## Troubleshooting

| Issue | Solution |
|-------|----------|
| {Problem} | {Fix} |
```

## Validation Rules

### E020: Missing frontmatter
```
Error: Command file must have valid YAML frontmatter
```

### E021: Missing description
```
Error: Command must have 'description' in frontmatter
```

### W020: No argument-hint
```
Info: Consider adding argument-hint for better UX in /help
```

### W021: File doesn't end with .md
```
Error: Command files must end with .md extension
```

## Examples

### Minimal Command

```yaml
---
description: Run all validation checks
---

# /validate Command

Runs schema and registration validation.

## Usage

```
/validate
/validate --fix
```
```

### Full-Featured Command

```yaml
---
description: Interactive wizard for creating Claude Code components
argument-hint: "[component description or 'help']"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Skill", "Task"]
---

# /assist Command

Smart scaffolding wizard with phase-aware guidance.

## Usage

```
/assist "코드 리뷰 자동화 기능"
/assist skill: "FEM analysis methodology"
/assist help
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| description | No | Natural language description of desired component |
| `skill:` prefix | No | Force skill type |
| `agent:` prefix | No | Force agent type |
| `help` | No | Show detailed help |

## Workflow

1. **Intent Phase**: Determine CREATE/REFACTOR/VERIFY
2. **Semantic Phase**: Classify component type
3. **Execute Phase**: Generate files
4. **Verify Phase**: Validate against schema

## Examples

### Create a Skill

```
/assist "FEM 해석 방법론 스킬"
```

Creates:
- `skills/fem-analysis/SKILL.md`
- `skills/fem-analysis/references/`

### Create an Agent

```
/assist "코드 리뷰 자동화 에이전트"
```

Creates:
- `agents/code-reviewer.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Phase stuck" | Run `/assist help` to reset |
| "Wrong type detected" | Use prefix: `/assist skill: ...` |
```

### Command with Skills Loading

```yaml
---
description: Diagnose plugin issues
argument-hint: "[issue description]"
allowed-tools: ["Read", "Bash", "Grep", "Glob", "Skill"]
---

# /diagnose Command

Analyzes plugin structure and identifies issues.

## Usage

```
/diagnose
/diagnose "hooks not firing"
```

## Workflow

1. Load diagnostic skills:
   ```
   Skill("assist-plugin:phase-verify")
   ```
2. Run validation scripts
3. Present findings with fix suggestions
```

## Naming Convention

| Pattern | Example | Notes |
|---------|---------|-------|
| Action verb | `validate.md` | Preferred for single actions |
| Noun | `wizard.md` | OK for multi-step workflows |
| Kebab-case | `run-tests.md` | Required for multi-word |

## Integration with Hooks

Commands can trigger hook chains:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/validate_before_bash.py"
          }
        ]
      }
    ]
  }
}
```
