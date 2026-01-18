# Skill Schema Reference

## Directory Structure (REQUIRED)

```
skills/{skill-name}/
├── SKILL.md              # Required: Core instructions
├── references/           # Optional: Detailed documentation
│   ├── advanced.md
│   └── examples.md
├── scripts/              # Optional: Executable code
│   └── helper.py
└── assets/               # Optional: Templates, images
```

## SKILL.md Frontmatter (REQUIRED)

```yaml
---
name: skill-name                    # kebab-case, matches directory
description: "When to use this"     # Triggers skill loading
allowed-tools: ["Read", "Grep"]     # Tool restrictions
---
```

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | ✅ | string | Unique identifier, kebab-case |
| `description` | ✅ | string | Trigger phrases for skill loading |
| `allowed-tools` | ❌ | array | Restrict available tools |

### Tool Restriction Patterns

```yaml
# Knowledge skill (read-only)
allowed-tools: ["Read", "Grep", "Glob"]

# Hybrid skill (read + write)
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash"]

# Tool skill (full access)
allowed-tools: ["Read", "Write", "Bash", "Task"]
```

## SKILL.md Body Structure

```markdown
# Skill Name

[2-3 sentence overview - what this skill helps with]

## When to Use

- Trigger condition 1
- Trigger condition 2

## Quick Start

[Fastest path to value - 3-5 steps max]

## Workflow

1. Step 1
2. Step 2
3. Step 3

## Scripts (if applicable)

| Script | Purpose | Usage |
|--------|---------|-------|
| helper.py | Does X | `python3 scripts/helper.py --arg` |

## Key Principles

- Principle 1
- Principle 2

## References

For advanced usage: [references/advanced.md](references/advanced.md)
```

## Skill Types

| Type | Freedom | Structure | Use When |
|------|---------|-----------|----------|
| Knowledge | High | SKILL.md + references/ | Multiple approaches, context-dependent |
| Hybrid | Medium | SKILL.md + scripts/ + references/ | Guidance + automation needed |
| Tool | Low | SKILL.md + scripts/ | Deterministic, repeatable ops |
| Expert | Very Low | Full + validation/ | Complex internals, undocumented APIs |

## Validation Rules

### E001: Missing SKILL.md
```
Error: skills/{name}/ must contain SKILL.md
```

### E002: Invalid frontmatter
```
Error: SKILL.md must have valid YAML frontmatter with name and description
```

### W001: SKILL.md too long
```
Warning: SKILL.md should be < 500 words (currently {n} words)
```

### W002: Missing description triggers
```
Warning: description should include trigger phrases for skill loading
```

## Examples

### Minimal Knowledge Skill

```yaml
---
name: code-review
description: Code review best practices. Use when reviewing code or PRs.
allowed-tools: ["Read", "Grep", "Glob"]
---

# Code Review

Guidelines for effective code reviews.

## Quick Start

1. Read the diff
2. Check for patterns in references/
3. Provide structured feedback

## Key Principles

- Focus on logic, not style
- Be constructive

For detailed patterns: [references/patterns.md](references/patterns.md)
```

### Hybrid Skill with Scripts

```yaml
---
name: schema-validation
description: Validate JSON/YAML schemas. Use when checking configuration files.
allowed-tools: ["Read", "Write", "Bash"]
---

# Schema Validation

Automated schema checking with manual override options.

## Quick Start

```bash
python3 scripts/validate.py --file config.json
```

## Scripts

| Script | Purpose |
|--------|---------|
| validate.py | Run schema validation |
| fix.py | Auto-fix common issues |
```
