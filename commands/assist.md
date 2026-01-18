---
description: Create Claude Code components (skill, agent, command, hook, MCP) with phase-aware guidance
argument-hint: "[component description or 'help']"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Skill", "Task"]
---

# /assist Command

Smart scaffolding for Claude Code plugin components with 4-phase workflow.

## Usage

```
/assist "코드 리뷰 자동화 기능"
/assist "SAP2000 MCP gateway"
/assist help
```

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: INTENT     → Create vs Refactor/Verify 판단          │
│  Phase 2: SEMANTIC   → 적절한 컴포넌트 타입 결정               │
│  Phase 3: EXECUTE    → 스키마 기반 파일 생성                   │
│  Phase 4: VERIFY     → EXIT GATE - 스키마 검증 (강제)          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

1. Run `/assist` with your requirement
2. Answer 2-3 clarifying questions
3. Review generated component
4. Verify passes automatically (or fix issues)

## Phase Details

### Phase 1: Intent Classification

Determines operation type:

| Intent | Triggers | Action |
|--------|----------|--------|
| CREATE | "만들어", "create", "new", "추가" | New component scaffolding |
| REFACTOR | "수정", "개선", "refactor", "fix" | Modify existing component |
| VERIFY | "검증", "validate", "check" | Schema validation only |

### Phase 2: Semantic Analysis

Determines component type based on your description:

| Component | When to Use | Key Indicators |
|-----------|-------------|----------------|
| **Skill** | Reusable knowledge/methodology | "방법", "가이드", "패턴" |
| **Agent** | Multi-step autonomous tasks | "자동화", "분석", "에이전트" |
| **Command** | User-initiated actions | "명령어", "/커맨드", "실행" |
| **Hook** | Event-driven enforcement | "강제", "검증", "방지" |
| **MCP** | External tool integration | "API", "서버", "MCP" |

### Phase 3: Execute

Loads appropriate schema and generates files:

```
Skill("assist-plugin:phase-execute")
→ Load component-specific schema
→ Generate SKILL.md / agent.md / command.md / hook.json
→ Create directory structure
```

### Phase 4: Verify (EXIT GATE)

**MANDATORY** - Cannot skip this phase.

```bash
python3 scripts/schema_validator.py --component-type {type} --path {path}
```

- Schema validation errors → BLOCK, show fix suggestions
- Warnings → Allow with notice
- Pass → Complete workflow

## Monitor Panel (tmux)

When running in tmux, a side panel shows:

```
┌──────────────────────────┐
│  📊 Assist Workflow      │
│  ────────────────────    │
│  Phase: semantic [2/4]   │
│  ████████░░░░░░░ 50%     │
│                          │
│  ┌─ Intent    ✓          │
│  ├─ Semantic  ◀ current  │
│  ├─ Execute   ○          │
│  └─ Verify    ○          │
│                          │
│  Decision:               │
│  • Type: Hook + Skill    │
│  • Reason: 자동 트리거   │
│    + 지식 기반 분석      │
└──────────────────────────┘
```

## Examples

### Create a new skill

```
/assist "FEM 해석 방법론 스킬"
```

→ Creates `skills/fem-analysis/SKILL.md` with proper frontmatter

### Create an agent

```
/assist "코드 리뷰 자동화 에이전트"
```

→ Creates `agents/code-reviewer.md` with tools and skills

### Create a hook

```
/assist "커밋 전 린트 강제 훅"
```

→ Creates `hooks/pre-commit-lint.json` with PreToolUse config

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Phase stuck" | Check `scripts/workflow_state.py status` |
| "Verify failed" | Read error message, fix schema issues |
| "Wrong component type" | Re-run with explicit type: `/assist skill: ...` |

## References

- Phase 1: `Skill("assist-plugin:phase-intent")`
- Phase 2: `Skill("assist-plugin:phase-semantic")`
- Phase 3: `Skill("assist-plugin:phase-execute")`
- Phase 4: `Skill("assist-plugin:phase-verify")`
