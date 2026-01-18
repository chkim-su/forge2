# Agent Schema Reference

## File Structure

```
agents/{agent-name}.md    # Single file with frontmatter + body
```

## Frontmatter (REQUIRED)

```yaml
---
name: agent-name
description: "What this agent does"
tools: ["Read", "Write", "Bash"]
skills: skill-a, skill-b
model: sonnet
---
```

### Frontmatter Fields

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `name` | ✅ | string | - | Unique identifier, kebab-case |
| `description` | ✅ | string | - | What the agent does |
| `tools` | ⚠️ | array/omit | all | Tool restrictions (see below) |
| `skills` | ❌ | string | - | Comma-separated skill names |
| `model` | ❌ | string | sonnet | opus, sonnet, haiku |

### Tools Field Behavior (CRITICAL)

```yaml
# ❌ NO tools (pure reasoning, no MCP)
tools: []

# ✅ ALL tools including MCP (default)
# Omit the field entirely:
name: my-agent
description: ...
# (no tools field)

# ⚠️ SPECIFIC tools only (NO MCP unless listed)
tools: ["Read", "Write", "Bash"]

# ✅ SPECIFIC tools WITH MCP
tools: ["Read", "Write", "mcp__serena__*"]
```

| tools: Setting | MCP Access | Use When |
|----------------|------------|----------|
| Omitted | ✅ All | Agent needs full autonomy |
| `[]` | ❌ None | Pure analysis, no side effects |
| `["Read", "Write"]` | ❌ None | Controlled file access |
| `["Read", "mcp__*"]` | ✅ Listed | Specific MCP servers |

## Body Structure

```markdown
# {Agent Name} Agent

[Overview: what this agent accomplishes]

## Trigger

[When this agent should be invoked]

## Process

1. {Step 1 - what it does first}
2. {Step 2 - analysis/decision}
3. {Step 3 - action/output}

## Input

[Expected input format or context]

## Output

[What the agent produces]

## Skills Used

- `{skill-1}`: {why it's needed}
- `{skill-2}`: {why it's needed}
```

## Validation Rules

### E010: Missing frontmatter
```
Error: Agent file must have valid YAML frontmatter
```

### E011: Missing required fields
```
Error: Agent must have 'name' and 'description' in frontmatter
```

### W010: tools field empty but description implies tool use
```
Warning: tools: [] but description mentions "write", "create", "execute"
This agent won't be able to perform those actions.
```

### W011: No skills specified
```
Warning: Agent has no skills. Consider loading relevant skills for context.
```

### W012: Model not specified
```
Info: Model defaulting to 'sonnet'. Specify 'opus' for complex reasoning.
```

## Examples

### Minimal Agent

```yaml
---
name: code-reviewer
description: Reviews code changes and provides feedback
tools: ["Read", "Grep"]
---

# Code Reviewer Agent

Reviews code for quality and suggests improvements.

## Process

1. Read the changed files
2. Analyze for patterns
3. Output structured feedback
```

### Full-Featured Agent

```yaml
---
name: skill-architect
description: Designs and creates new skills based on requirements
tools: ["Read", "Write", "Bash", "Grep", "Glob"]
skills: skill-design, orchestration-patterns
model: opus
---

# Skill Architect Agent

Autonomous agent that designs skill structure based on user requirements.

## Trigger

Invoked when user wants to create a new skill.

## Process

1. Analyze requirements (2-3 clarifying questions)
2. Classify skill type (Knowledge/Hybrid/Tool/Expert)
3. Generate SKILL.md with proper frontmatter
4. Create reference files if needed
5. Validate generated structure

## Input

- User's description of desired functionality
- Context about existing skills (if any)

## Output

- Complete skill directory structure
- Validated SKILL.md
- Reference documentation

## Skills Used

- `skill-design`: Structure and type guidelines
- `orchestration-patterns`: Multi-skill coordination
```

### Agent with MCP Access

```yaml
---
name: serena-analyzer
description: Analyzes codebase using Serena MCP for semantic understanding
tools: ["Read", "Grep", "mcp__serena__*"]
skills: mcp-daemon-isolation
model: sonnet
---

# Serena Analyzer Agent

Uses Serena MCP for deep code analysis.

## Process

1. Connect to Serena daemon (mcp__serena__find_symbol)
2. Analyze code structure
3. Generate insights
```
