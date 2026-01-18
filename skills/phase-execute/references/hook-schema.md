# Hook Schema Reference

## File Structure

```
hooks/
├── hooks.json          # Main hook configuration
└── README.md           # Optional: Hook documentation
```

## hooks.json Schema (Claude Code 1.0.40+)

```json
{
  "$comment": "Optional description",
  "hooks": {
    "{EventType}": [
      {
        "matcher": "{ToolPattern}",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/{script}.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Event Types

| Event | When Fired | Can Block | Use For |
|-------|------------|-----------|---------|
| `UserPromptSubmit` | User sends message | No | Context injection, state init |
| `PreToolUse` | Before tool executes | **Yes** (exit 2) | Validation, prevention |
| `PostToolUse` | After tool executes | No | Side effects, logging |
| `Stop` | Claude finishes response | No | Cleanup, final validation |
| `SessionStart` | Session begins | No | Service startup |

## Matcher Patterns

```json
// Single tool
"matcher": "Write"

// Multiple tools (OR)
"matcher": "Write|Edit"

// All tools (regex)
"matcher": ".*"

// Specific pattern
"matcher": "Bash|Task"
```

## Exit Codes (CRITICAL)

| Exit Code | PreToolUse/Stop | PostToolUse |
|-----------|-----------------|-------------|
| 0 | ✅ Allow | Continue |
| 2 | ❌ **BLOCK** (stderr → Claude) | Logged only |
| 1, 3+ | ❌ **BLOCK** | Logged only |

### Blocking Example (PreToolUse)

```python
#!/usr/bin/env python3
import sys

# Check condition
if not valid:
    print("❌ Blocked: reason here", file=sys.stderr)
    sys.exit(2)  # BLOCK the tool

print("✅ Allowed")
sys.exit(0)  # ALLOW the tool
```

## Hook Types

| Role | Event | Example Use |
|------|-------|-------------|
| **Gate** | PreToolUse | Block dangerous commands |
| **Validator** | PostToolUse | Check output validity |
| **Side Effect** | PostToolUse | Auto-format, auto-commit |
| **State Manager** | Any | Track workflow phases |
| **Context Injector** | UserPromptSubmit | Load skills, set context |

## Environment Variables

Available in hook scripts:

| Variable | Description |
|----------|-------------|
| `CLAUDE_PLUGIN_ROOT` | Plugin root directory |
| `TOOL_NAME` | Current tool name (PreToolUse/PostToolUse) |
| `TOOL_INPUT` | JSON of tool input |
| `TOOL_OUTPUT` | JSON of tool output (PostToolUse only) |

## Validation Rules

### E030: Invalid JSON
```
Error: hooks.json must be valid JSON
```

### E031: Unknown event type
```
Error: Unknown event "{event}". Valid: UserPromptSubmit, PreToolUse, PostToolUse, Stop, SessionStart
```

### W030: Timeout too short
```
Warning: timeout < 3 may cause premature termination
```

### W031: No error handling in script
```
Warning: Hook script should handle errors gracefully
```

## Examples

### Simple Validation Gate

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/validate_before_write.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Multi-Hook Chain

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/check_dangerous_commands.py\"",
            "timeout": 3
          },
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/validate_state.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/auto_format.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Workflow State Management

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py\" init",
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_state.py\" finalize",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Context Injection

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/start_daemon.py\" &",
            "timeout": 5
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/inject_context.py\"",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

## Hookify Decision Rule

```
If requirement contains ["MUST", "REQUIRED", "CRITICAL", "강제", "반드시"]:
    → Implement as Hook (documentation alone WILL be ignored)

If requirement contains ["should", "consider", "recommend"]:
    → Documentation is sufficient
```

## Common Patterns

### Pattern 1: Pre-commit Lint

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "python3 scripts/check_lint_before_commit.py",
    "timeout": 10
  }]
}
```

### Pattern 2: Schema Validation Gate

```json
{
  "matcher": "Write|Edit",
  "hooks": [{
    "type": "command",
    "command": "python3 scripts/schema_validator.py --pre-edit",
    "timeout": 15
  }]
}
```

### Pattern 3: Exit Gate (Stop event)

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 scripts/verify_workflow_complete.py",
        "timeout": 10
      }]
    }]
  }
}
```
