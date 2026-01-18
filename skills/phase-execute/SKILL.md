---
name: phase-execute
description: Phase 3 of assist workflow - Generate component files using schema-based templates
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
---

# Phase 3: Execute

Generate component files based on determined type with proper schema compliance.

## Workflow

```
1. Load schema for component type
2. Gather required fields (ask user if needed)
3. Generate files with proper structure
4. Register in marketplace.json (if applicable)
```

## Component Schemas

| Component | Schema Reference | Required Fields |
|-----------|------------------|-----------------|
| Skill | [skill-schema.md](references/skill-schema.md) | name, description |
| Agent | [agent-schema.md](references/agent-schema.md) | name, description, tools |
| Command | [command-schema.md](references/command-schema.md) | description |
| Hook | [hook-schema.md](references/hook-schema.md) | event, matcher, command |
| MCP | [mcp-schema.md](references/mcp-schema.md) | name, transport |

## Generation Templates

### Skill Generation

```bash
# Create directory structure
mkdir -p skills/{name}
mkdir -p skills/{name}/references

# Generate SKILL.md
cat > skills/{name}/SKILL.md << 'EOF'
---
name: {name}
description: {description}
allowed-tools: {tools}
---

# {Title}

{overview}

## When to Use

- {trigger_1}
- {trigger_2}

## Quick Start

{quick_start}

## References

For detailed information: [references/details.md](references/details.md)
EOF
```

### Agent Generation

```bash
# Generate agent file
cat > agents/{name}.md << 'EOF'
---
name: {name}
description: {description}
tools: {tools}
skills: {skills}
model: {model}
---

# {Title} Agent

{overview}

## Process

1. {step_1}
2. {step_2}
3. {step_3}

## Output Format

{output_format}
EOF
```

### Command Generation

```bash
# Generate command file
cat > commands/{name}.md << 'EOF'
---
description: {description}
argument-hint: "{args}"
allowed-tools: {tools}
---

# /{name} Command

{overview}

## Usage

```
/{name} {usage_example}
```

## Workflow

{workflow}
EOF
```

### Hook Generation

```bash
# Add to hooks/hooks.json
python3 scripts/add_hook.py \
  --event {PreToolUse|PostToolUse|Stop|...} \
  --matcher "{tool_pattern}" \
  --command "python3 scripts/{script}.py" \
  --timeout {timeout}
```

### MCP Generation

```bash
# Generate .mcp.json entry
python3 scripts/add_mcp.py \
  --name {name} \
  --transport {stdio|sse} \
  --command "{command}"
```

## Field Collection

When required fields are missing, ask user:

```yaml
# For Skill
Missing: description
Q: "이 스킬은 어떤 상황에서 사용하나요? (언제 로드되어야 하는지 트리거 포함)"

# For Agent
Missing: tools
Q: "이 에이전트가 사용할 도구는? (비우면 모든 도구 사용, MCP 포함)"
Options:
  - "[]" → No tools (pure thinking)
  - "omit" → All tools including MCP
  - "[Read, Write, Bash]" → Specific tools only

# For Hook
Missing: event
Q: "어떤 이벤트에 실행되나요?"
Options:
  - PreToolUse → 도구 실행 전 (차단 가능)
  - PostToolUse → 도구 실행 후 (검증/부작용)
  - Stop → Claude 응답 완료 시
  - UserPromptSubmit → 사용자 입력 시
```

## Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Skill | kebab-case directory | `skills/code-review/` |
| Agent | kebab-case file | `agents/code-reviewer.md` |
| Command | kebab-case file | `commands/run-tests.md` |
| Hook script | kebab-case | `scripts/pre-commit-lint.py` |

## State Update

After generation:

```bash
python3 scripts/workflow_state.py add-file path/to/file1
python3 scripts/workflow_state.py add-file path/to/file2
python3 scripts/workflow_state.py update execute completed
```

## Output Format

```yaml
Phase: execute
Status: completed
Result:
  component_type: SKILL
  generated_files:
    - skills/code-review/SKILL.md
    - skills/code-review/references/guidelines.md
  registered: true  # Added to marketplace.json
  next_phase: verify
```

## Transition to Phase 4

```
Skill("assist-plugin:phase-verify")

→ Validate generated files against schema
→ Check marketplace.json registration
→ EXIT GATE enforcement
```
