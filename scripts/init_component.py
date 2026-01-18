#!/usr/bin/env python3
"""
Initialize new Claude Code plugin components.

Usage:
  init_component.py skill <name> [--description DESC]
  init_component.py agent <name> [--description DESC] [--tools TOOLS] [--model MODEL]
  init_component.py command <name> [--description DESC]
  init_component.py hook <event> <matcher> <script>
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))


def init_skill(name: str, description: str = None):
    """Initialize a new skill directory."""
    skill_dir = PLUGIN_ROOT / "skills" / name
    
    if skill_dir.exists():
        print(f"❌ Skill already exists: {skill_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create directories
    skill_dir.mkdir(parents=True)
    (skill_dir / "references").mkdir()
    
    # Default description
    if not description:
        description = f"{name.replace('-', ' ').title()} skill. Use when working with {name}."
    
    # Create SKILL.md
    skill_md = f"""---
name: {name}
description: {description}
allowed-tools: ["Read", "Grep", "Glob"]
---

# {name.replace('-', ' ').title()}

[Overview: what this skill helps with]

## When to Use

- Trigger condition 1
- Trigger condition 2

## Quick Start

1. Step 1
2. Step 2
3. Step 3

## Key Principles

- Principle 1
- Principle 2

## References

For detailed information: [references/details.md](references/details.md)
"""
    
    (skill_dir / "SKILL.md").write_text(skill_md)
    
    # Create placeholder reference
    (skill_dir / "references" / "details.md").write_text(f"# {name.title()} Details\n\n[Add detailed documentation here]")
    
    print(f"✅ Created skill: {skill_dir}")
    print(f"   - SKILL.md")
    print(f"   - references/details.md")
    
    # Update marketplace.json
    update_marketplace("skills", f"./skills/{name}")


def init_agent(name: str, description: str = None, tools: str = None, model: str = "sonnet"):
    """Initialize a new agent file."""
    agent_file = PLUGIN_ROOT / "agents" / f"{name}.md"
    
    if agent_file.exists():
        print(f"❌ Agent already exists: {agent_file}", file=sys.stderr)
        sys.exit(1)
    
    # Ensure directory exists
    agent_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Default description
    if not description:
        description = f"Agent for {name.replace('-', ' ')} tasks"
    
    # Tools field
    tools_line = ""
    if tools:
        tools_list = [t.strip() for t in tools.split(",")]
        tools_line = f'tools: {json.dumps(tools_list)}'
    
    # Create agent file
    agent_md = f"""---
name: {name}
description: {description}
{tools_line}
model: {model}
---

# {name.replace('-', ' ').title()} Agent

[Overview: what this agent accomplishes]

## Trigger

[When this agent should be invoked]

## Process

1. Step 1
2. Step 2
3. Step 3

## Input

[Expected input format]

## Output

[What the agent produces]
"""
    
    agent_file.write_text(agent_md.strip() + "\n")
    
    print(f"✅ Created agent: {agent_file}")
    
    # Update marketplace.json
    update_marketplace("agents", f"./agents/{name}.md")


def init_command(name: str, description: str = None):
    """Initialize a new command file."""
    cmd_file = PLUGIN_ROOT / "commands" / f"{name}.md"
    
    if cmd_file.exists():
        print(f"❌ Command already exists: {cmd_file}", file=sys.stderr)
        sys.exit(1)
    
    # Ensure directory exists
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Default description
    if not description:
        description = f"Execute {name.replace('-', ' ')} operation"
    
    # Create command file
    cmd_md = f"""---
description: {description}
argument-hint: "[options]"
---

# /{name} Command

[Overview: what this command does]

## Usage

```
/{name}
/{name} --option value
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--option` | No | Description |

## Workflow

1. Step 1
2. Step 2
3. Step 3

## Examples

### Example 1

```
/{name} example-usage
```
"""
    
    cmd_file.write_text(cmd_md)
    
    print(f"✅ Created command: {cmd_file}")
    
    # Update marketplace.json
    update_marketplace("commands", f"./commands/{name}.md")


def init_hook(event: str, matcher: str, script: str):
    """Add a new hook to hooks.json."""
    hooks_file = PLUGIN_ROOT / "hooks" / "hooks.json"
    
    # Valid events
    valid_events = ["UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionStart"]
    if event not in valid_events:
        print(f"❌ Invalid event: {event}. Valid: {valid_events}", file=sys.stderr)
        sys.exit(1)
    
    # Load existing hooks
    if hooks_file.exists():
        hooks_data = json.loads(hooks_file.read_text())
    else:
        hooks_file.parent.mkdir(parents=True, exist_ok=True)
        hooks_data = {"hooks": {}}
    
    # Ensure event exists
    if event not in hooks_data["hooks"]:
        hooks_data["hooks"][event] = []
    
    # Check if script exists
    script_path = PLUGIN_ROOT / "scripts" / script
    if not script_path.exists():
        print(f"⚠️  Warning: Script not found: {script_path}")
    
    # Create new hook entry
    new_hook = {
        "hooks": [{
            "type": "command",
            "command": f'python3 "${{CLAUDE_PLUGIN_ROOT}}/scripts/{script}"',
            "timeout": 10
        }]
    }
    
    if matcher and event in ["PreToolUse", "PostToolUse"]:
        new_hook["matcher"] = matcher
    
    # Add to hooks
    hooks_data["hooks"][event].append(new_hook)
    
    # Write back
    hooks_file.write_text(json.dumps(hooks_data, indent=2))
    
    print(f"✅ Added hook:")
    print(f"   Event: {event}")
    if matcher:
        print(f"   Matcher: {matcher}")
    print(f"   Script: {script}")


def update_marketplace(component_type: str, path: str):
    """Update marketplace.json with new component."""
    marketplace_file = PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"
    
    if not marketplace_file.exists():
        print(f"⚠️  marketplace.json not found, skipping registration")
        return
    
    try:
        data = json.loads(marketplace_file.read_text())
        
        if data.get("plugins") and len(data["plugins"]) > 0:
            plugin = data["plugins"][0]
            
            if component_type not in plugin:
                plugin[component_type] = []
            
            if path not in plugin[component_type]:
                plugin[component_type].append(path)
                marketplace_file.write_text(json.dumps(data, indent=2))
                print(f"   📝 Registered in marketplace.json")
    except Exception as e:
        print(f"⚠️  Failed to update marketplace.json: {e}")


def main():
    parser = argparse.ArgumentParser(description="Initialize Claude Code plugin components")
    subparsers = parser.add_subparsers(dest="type", required=True)
    
    # Skill subcommand
    skill_parser = subparsers.add_parser("skill", help="Create a new skill")
    skill_parser.add_argument("name", help="Skill name (kebab-case)")
    skill_parser.add_argument("--description", "-d", help="Skill description")
    
    # Agent subcommand
    agent_parser = subparsers.add_parser("agent", help="Create a new agent")
    agent_parser.add_argument("name", help="Agent name (kebab-case)")
    agent_parser.add_argument("--description", "-d", help="Agent description")
    agent_parser.add_argument("--tools", "-t", help="Comma-separated tool list")
    agent_parser.add_argument("--model", "-m", default="sonnet", choices=["opus", "sonnet", "haiku"])
    
    # Command subcommand
    cmd_parser = subparsers.add_parser("command", help="Create a new command")
    cmd_parser.add_argument("name", help="Command name (kebab-case)")
    cmd_parser.add_argument("--description", "-d", help="Command description")
    
    # Hook subcommand
    hook_parser = subparsers.add_parser("hook", help="Add a new hook")
    hook_parser.add_argument("event", help="Hook event type")
    hook_parser.add_argument("matcher", nargs="?", default="", help="Tool matcher pattern")
    hook_parser.add_argument("script", help="Script filename")
    
    args = parser.parse_args()
    
    if args.type == "skill":
        init_skill(args.name, args.description)
    elif args.type == "agent":
        init_agent(args.name, args.description, args.tools, args.model)
    elif args.type == "command":
        init_command(args.name, args.description)
    elif args.type == "hook":
        init_hook(args.event, args.matcher, args.script)


if __name__ == "__main__":
    main()
