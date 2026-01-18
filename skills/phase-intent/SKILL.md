---
name: phase-intent
description: Phase 1 of assist workflow - Classify intent as CREATE, REFACTOR, or VERIFY
allowed-tools: ["Read", "Grep", "Glob"]
---

# Phase 1: Intent Classification

Determine what operation the user wants to perform.

## Intent Types

| Intent | Keywords (EN) | Keywords (KR) | Action |
|--------|---------------|---------------|--------|
| **CREATE** | create, new, make, add, build | 만들어, 생성, 추가, 새로운 | New component from scratch |
| **REFACTOR** | fix, improve, modify, update, refactor | 수정, 개선, 고쳐, 업데이트 | Modify existing component |
| **VERIFY** | check, validate, verify, test | 검증, 확인, 테스트, 체크 | Validate without changes |

## Classification Logic

```python
def classify_intent(user_input: str) -> str:
    input_lower = user_input.lower()
    
    # CREATE indicators
    create_keywords = [
        "create", "new", "make", "add", "build", "generate",
        "만들", "생성", "추가", "새로"
    ]
    
    # REFACTOR indicators
    refactor_keywords = [
        "fix", "improve", "modify", "update", "refactor", "change",
        "수정", "개선", "고쳐", "변경", "업데이트"
    ]
    
    # VERIFY indicators
    verify_keywords = [
        "check", "validate", "verify", "test", "review",
        "검증", "확인", "테스트", "체크", "점검"
    ]
    
    # Score each intent
    scores = {
        "CREATE": sum(1 for k in create_keywords if k in input_lower),
        "REFACTOR": sum(1 for k in refactor_keywords if k in input_lower),
        "VERIFY": sum(1 for k in verify_keywords if k in input_lower)
    }
    
    # Check for existing file reference (suggests REFACTOR)
    if any(p in input_lower for p in ["existing", "current", "this", "기존", "현재"]):
        scores["REFACTOR"] += 2
    
    # Default to CREATE if ambiguous
    max_score = max(scores.values())
    if max_score == 0:
        return "CREATE"
    
    return max(scores, key=scores.get)
```

## Contextual Signals

### Strong CREATE signals
- No existing files mentioned
- "from scratch", "처음부터"
- Component name not found in project

### Strong REFACTOR signals
- File path provided
- "this", "current", "existing"
- Component already exists in project

### Strong VERIFY signals
- "is it correct", "맞아?"
- "check if", "확인해줘"
- No modification language

## State Update

After classification, update workflow state:

```bash
python3 scripts/workflow_state.py set-phase intent completed
python3 scripts/workflow_state.py set-intent {CREATE|REFACTOR|VERIFY}
```

## Output Format

```yaml
Phase: intent
Status: completed
Result:
  intent: CREATE  # or REFACTOR, VERIFY
  confidence: high  # high, medium, low
  signals:
    - "만들어" keyword detected
    - No existing component found
  next_phase: semantic
```

## Edge Cases

| Situation | Resolution |
|-----------|------------|
| Mixed signals | Ask user for clarification |
| No keywords | Default to CREATE |
| Ambiguous ("help with") | Check context, default CREATE |

## Transition to Phase 2

Once intent is classified:

```
IF intent == CREATE:
    → Skill("assist-plugin:phase-semantic")
    
IF intent == REFACTOR:
    → Locate existing component first
    → Then Skill("assist-plugin:phase-semantic")
    
IF intent == VERIFY:
    → Skip to Skill("assist-plugin:phase-verify")
```
