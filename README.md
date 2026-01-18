# Assist Plugin

**Phase-aware workflow for creating Claude Code components**

Smart scaffolding tool with 4-phase workflow: Intent → Semantic → Execute → Verify (EXIT GATE)

## Installation

```bash
claude plugin add /path/to/forge-editor
```

## Quick Start

```bash
# Start the assistant
/assist "코드 리뷰 자동화 기능"

# Or with explicit type
/assist skill: "FEM 해석 방법론"
/assist agent: "자동 코드 리뷰어"
/assist hook: "커밋 전 린트 검사"
```

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: INTENT     → CREATE / REFACTOR / VERIFY 판단         │
│  Phase 2: SEMANTIC   → SKILL / AGENT / COMMAND / HOOK / MCP    │
│  Phase 3: EXECUTE    → 스키마 기반 파일 생성                   │
│  Phase 4: VERIFY     → EXIT GATE (강제 검증)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Skills

| Skill | Description |
|-------|-------------|
| `phase-intent` | Intent classification logic |
| `phase-semantic` | Component type decision matrix |
| `phase-execute` | Schema templates and generation |
| `phase-verify` | Validation rules and EXIT GATE |

### Commands

| Command | Description |
|---------|-------------|
| `/assist` | Main entry point for component creation |

### Agents

| Agent | Description |
|-------|-------------|
| `component-architect` | Autonomous component designer |
| `phase-semantic-agent` | Component type determination |
| `phase-execute-agent` | Schema-based file generation |
| `phase-verify-agent` | EXIT GATE validation |

## Directory Structure

```
forge-editor/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   ├── phase-intent/
│   ├── phase-semantic/
│   ├── phase-execute/
│   └── phase-verify/
├── commands/
│   └── assist.md
├── agents/
│   └── component-architect.md
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── semantic-intent-router-hook.py
│   ├── enforce_workflow.py
│   ├── task-post-router.py
│   ├── workflow_state.py
│   ├── schema_validator.py
│   └── exit_gate.py
└── README.md
```

## Schema References

Each component type has a schema in `skills/phase-execute/references/`:

- `skill-schema.md` - Skill structure and frontmatter
- `agent-schema.md` - Agent configuration
- `command-schema.md` - Command definition
- `hook-schema.md` - Hook configuration

## Hook Enforcement

Workflow phases are enforced via hooks:

| Hook | Event | Purpose |
|------|-------|---------|
| `semantic-intent-router-hook.py` | UserPromptSubmit | Intent analysis, workflow init |
| `enforce_workflow.py` | PreToolUse | Block tools until agent runs |
| `task-post-router.py` | PostToolUse (Task) | Detect agent completion |
| `schema_validator.py` | PostToolUse (Write/Edit) | Validate changes |
| `exit_gate.py` | Stop | **EXIT GATE** enforcement |

## Development

### Testing Workflow State

```bash
# Initialize workflow
python3 scripts/workflow_state.py init skill_creation

# Check status
python3 scripts/workflow_state.py status

# Update phase status
python3 scripts/workflow_state.py update semantic completed

# Set intent/component type
python3 scripts/workflow_state.py set-intent CREATE
python3 scripts/workflow_state.py set-component SKILL

# Track generated files
python3 scripts/workflow_state.py add-file skills/my-skill/SKILL.md

# Reset workflow
python3 scripts/workflow_state.py reset
```

### Running Validation

```bash
# Validate all
python3 scripts/schema_validator.py

# Validate specific component
python3 scripts/schema_validator.py --path skills/my-skill --type skill

# Strict mode (warnings = errors)
python3 scripts/schema_validator.py --strict
```

## License

MIT
