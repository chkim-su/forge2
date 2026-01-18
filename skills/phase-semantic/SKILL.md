---
name: phase-semantic
description: Phase 2 of assist workflow - Determine appropriate component type (Skill, Agent, Command, Hook, MCP)
allowed-tools: ["Read", "Grep", "Glob"]
---

# Phase 2: Semantic Analysis

Determine which component type best fits the user's requirement.

## Component Type Decision Matrix

| Component | Primary Use | Key Indicators | Freedom Level |
|-----------|-------------|----------------|---------------|
| **Skill** | Reusable knowledge/methodology | "방법", "가이드", "패턴", "how to" | High |
| **Agent** | Multi-step autonomous tasks | "자동화", "분석해", "agent", 복합 작업 | Medium |
| **Command** | User-initiated workflow | "/명령어", "실행", "run", 사용자 트리거 | Medium |
| **Hook** | Event-driven enforcement | "강제", "방지", "검증", "반드시" | Low |
| **MCP** | External tool integration | "API", "서버", "MCP", "외부 도구" | Very Low |

## Decision Algorithm

```
User Request
     │
     ├─ Contains "강제/반드시/must/prevent" ?
     │     └─ YES → HOOK (enforcement required)
     │
     ├─ Contains "API/MCP/서버/external" ?
     │     └─ YES → MCP (external integration)
     │
     ├─ Contains "자동/autonomous/multi-step" ?
     │     └─ YES → AGENT (complex automation)
     │
     ├─ Contains "/명령어/command/실행" ?
     │     └─ YES → COMMAND (user-initiated)
     │
     └─ DEFAULT → SKILL (knowledge/methodology)
```

## Detailed Indicators

### SKILL Indicators
```
Strong signals:
- "방법론", "methodology", "best practice"
- "가이드", "guide", "how to"
- "패턴", "pattern", "approach"
- "지식", "knowledge", "reference"
- Reusable across multiple contexts

Structure:
  skills/{name}/
  ├── SKILL.md          # Core instructions (<500 words)
  ├── references/       # Detailed docs
  └── scripts/          # Optional automation
```

### AGENT Indicators
```
Strong signals:
- "자동화", "automate", "autonomous"
- "분석해", "analyze", "review"
- "에이전트", "agent", "subagent"
- Multi-step workflow implied
- Needs to make decisions

Structure:
  agents/{name}.md      # Single file with frontmatter
  
Frontmatter:
  name: agent-name
  description: What it does
  tools: ["Read", "Write", "Bash"]  # or empty for all
  skills: skill-a, skill-b          # Skills to load
  model: sonnet                     # or opus, haiku
```

### COMMAND Indicators
```
Strong signals:
- "/명령어", "/command"
- "실행", "run", "execute"
- User explicitly triggers
- One-shot operation
- Entry point to workflow

Structure:
  commands/{name}.md    # Single file with frontmatter
  
Frontmatter:
  description: What this command does
  argument-hint: "[args]"
  allowed-tools: ["Read", "Write"]
```

### HOOK Indicators
```
Strong signals:
- "강제", "must", "enforce"
- "방지", "prevent", "block"
- "검증", "validate", "check"
- "반드시", "required", "mandatory"
- Event-driven (before/after tool use)

Structure:
  hooks/hooks.json      # Configuration file
  scripts/{hook}.py     # Hook implementation
```

### MCP Indicators
```
Strong signals:
- "API", "external API"
- "MCP", "서버", "server"
- "외부 도구", "external tool"
- "integration", "연동"
- Stateful connection needed

Structure:
  .mcp.json             # MCP configuration
  scripts/mcp-{name}/   # Server implementation
```

## Combination Patterns

Sometimes multiple components are needed:

| Pattern | Components | Example |
|---------|------------|---------|
| Knowledge + Automation | Skill + Agent | "FEM 분석 자동화" |
| User-triggered + Enforcement | Command + Hook | "린트 검사 명령어" |
| External + Knowledge | MCP + Skill | "SAP2000 API 가이드" |
| Full workflow | Command + Agent + Hook | "배포 파이프라인" |

## Disambiguation Questions

When unclear, ask ONE of these:

```yaml
# When Skill vs Agent unclear
Q: "이 기능이 지식/가이드를 제공하나요, 아니면 자동으로 작업을 수행하나요?"
A1: 지식/가이드 → SKILL
A2: 자동 수행 → AGENT

# When Command vs Hook unclear  
Q: "사용자가 직접 실행하나요, 아니면 특정 이벤트에 자동 실행되나요?"
A1: 직접 실행 → COMMAND
A2: 자동 실행 → HOOK

# When single vs combo unclear
Q: "이 기능에 강제(enforcement) 요소가 있나요?"
A1: 있음 → Add HOOK to combo
A2: 없음 → Single component
```

## State Update

After classification:

```bash
python3 scripts/workflow_state.py set-phase semantic completed
python3 scripts/workflow_state.py set-component-type {SKILL|AGENT|COMMAND|HOOK|MCP}
python3 scripts/workflow_state.py set-decision '{"type": "...", "reason": "..."}'
```

## Output Format

```yaml
Phase: semantic
Status: completed
Result:
  component_type: SKILL  # or AGENT, COMMAND, HOOK, MCP
  combination: null      # or ["SKILL", "HOOK"] for combo
  confidence: high
  reasoning:
    - "방법론" keyword detected → SKILL indicator
    - No enforcement language → no HOOK needed
    - Single component sufficient
  next_phase: execute
```

## Transition to Phase 3

```
Skill("assist-plugin:phase-execute")

→ Load schema for determined component type
→ Generate appropriate structure
```
