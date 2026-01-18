#!/usr/bin/env python3
"""
Schema validator for assist-plugin components.

Validates skills, agents, commands, and hooks against their schemas.

Usage:
  schema_validator.py [options]

Options:
  --path PATH         Specific file/directory to validate
  --type TYPE         Component type (skill, agent, command, hook)
  --pre-edit          Pre-edit validation (lighter checks)
  --post-edit         Post-edit validation (full checks)
  --strict            Treat warnings as errors
  --quiet             Minimal output
  --fix               Auto-fix issues
  --dry-run           Show fixes without applying
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Get plugin root
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))


class ValidationResult:
    def __init__(self):
        self.errors: List[Tuple[str, str]] = []      # (code, message)
        self.warnings: List[Tuple[str, str]] = []    # (code, message)
        self.info: List[str] = []
        self.fixed: List[str] = []
    
    def add_error(self, code: str, message: str):
        self.errors.append((code, message))
    
    def add_warning(self, code: str, message: str):
        self.warnings.append((code, message))
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def is_valid(self, strict: bool = False) -> bool:
        if self.has_errors():
            return False
        if strict and self.has_warnings():
            return False
        return True


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    
    try:
        import yaml
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter, body
    except:
        # Fallback: simple parsing
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip('"').strip("'")
        return frontmatter, parts[2].strip()


def validate_skill(path: Path, result: ValidationResult):
    """Validate a skill directory."""
    skill_md = path / "SKILL.md"
    
    # E001: SKILL.md must exist
    if not skill_md.exists():
        result.add_error("E001", f"Missing SKILL.md in {path}")
        return
    
    content = skill_md.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    
    # E002: Valid frontmatter required
    if frontmatter is None:
        result.add_error("E002", f"Invalid or missing frontmatter in {skill_md}")
        return
    
    # E003: Required fields
    if "name" not in frontmatter:
        result.add_error("E003", f"Missing 'name' in frontmatter: {skill_md}")
    
    if "description" not in frontmatter:
        result.add_error("E003", f"Missing 'description' in frontmatter: {skill_md}")
    
    # W001: Word count check
    word_count = len(body.split())
    if word_count > 500:
        result.add_warning("W001", f"SKILL.md has {word_count} words (recommended < 500)")
    
    # W002: Name should match directory
    if frontmatter.get("name") != path.name:
        result.add_warning("W002", f"Skill name '{frontmatter.get('name')}' doesn't match directory '{path.name}'")
    
    # Check references exist
    if "references/" in body:
        refs_dir = path / "references"
        if not refs_dir.exists():
            result.add_warning("W003", f"references/ mentioned but directory doesn't exist")


def validate_agent(path: Path, result: ValidationResult):
    """Validate an agent file."""
    if not path.exists():
        result.add_error("E010", f"Agent file not found: {path}")
        return
    
    if not path.name.endswith(".md"):
        result.add_error("E011", f"Agent file must end with .md: {path}")
        return
    
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    
    # E012: Valid frontmatter required
    if frontmatter is None:
        result.add_error("E012", f"Invalid or missing frontmatter in {path}")
        return
    
    # E013: Required fields
    if "name" not in frontmatter:
        result.add_error("E013", f"Missing 'name' in frontmatter: {path}")
    
    if "description" not in frontmatter:
        result.add_error("E013", f"Missing 'description' in frontmatter: {path}")
    
    # W010: Check tools field implications
    tools = frontmatter.get("tools")
    if tools == []:
        # Empty tools means no tool access
        body_lower = body.lower()
        action_words = ["write", "create", "execute", "run", "bash", "generate"]
        for word in action_words:
            if word in body_lower:
                result.add_warning("W010", f"tools: [] but description mentions '{word}'")
                break
    
    # W011: Model check
    model = frontmatter.get("model", "sonnet")
    valid_models = ["opus", "sonnet", "haiku"]
    if model not in valid_models:
        result.add_warning("W011", f"Unknown model '{model}'. Valid: {valid_models}")


def validate_command(path: Path, result: ValidationResult):
    """Validate a command file."""
    if not path.exists():
        result.add_error("E020", f"Command file not found: {path}")
        return
    
    if not path.name.endswith(".md"):
        result.add_error("E021", f"Command file must end with .md: {path}")
        return
    
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    
    # E022: Valid frontmatter required
    if frontmatter is None:
        result.add_error("E022", f"Invalid or missing frontmatter in {path}")
        return
    
    # E023: Required fields
    if "description" not in frontmatter:
        result.add_error("E023", f"Missing 'description' in frontmatter: {path}")


def validate_hooks(path: Path, result: ValidationResult):
    """Validate a hooks.json file."""
    if not path.exists():
        result.add_error("E030", f"Hooks file not found: {path}")
        return
    
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.add_error("E031", f"Invalid JSON in {path}: {e}")
        return
    
    hooks = content.get("hooks", {})
    valid_events = ["UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionStart"]
    
    for event in hooks.keys():
        if event.startswith("$"):
            continue  # Skip comments
        
        if event not in valid_events:
            result.add_error("E032", f"Unknown event type '{event}'. Valid: {valid_events}")
        
        # Check hook entries
        for entry in hooks.get(event, []):
            hook_list = entry.get("hooks", [])
            for hook in hook_list:
                # Check timeout
                timeout = hook.get("timeout", 10)
                if timeout < 3:
                    result.add_warning("W030", f"Timeout {timeout}s may be too short for {event}")
                
                # Check script exists
                command = hook.get("command", "")
                script_match = re.search(r'scripts/([^"]+\.py)', command)
                if script_match:
                    script_name = script_match.group(1)
                    script_path = PLUGIN_ROOT / "scripts" / script_name
                    if not script_path.exists():
                        result.add_warning("W031", f"Script not found: {script_name}")


def validate_marketplace(result: ValidationResult):
    """Validate marketplace.json and component registration."""
    marketplace_path = PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"
    
    if not marketplace_path.exists():
        result.add_error("E040", "marketplace.json not found")
        return
    
    try:
        content = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.add_error("E041", f"Invalid JSON in marketplace.json: {e}")
        return
    
    plugins = content.get("plugins", [])
    if not plugins:
        result.add_warning("W040", "No plugins defined in marketplace.json")
        return
    
    plugin = plugins[0]
    
    # Check skills registration
    registered_skills = plugin.get("skills", [])
    skills_dir = PLUGIN_ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                skill_path = f"./skills/{skill_dir.name}"
                if skill_path not in registered_skills:
                    result.add_warning("W041", f"Skill not registered: {skill_dir.name}")
    
    # Check commands registration
    registered_commands = plugin.get("commands", [])
    commands_dir = PLUGIN_ROOT / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            cmd_path = f"./commands/{cmd_file.name}"
            if cmd_path not in registered_commands:
                result.add_warning("W042", f"Command not registered: {cmd_file.name}")
    
    # Check agents registration
    registered_agents = plugin.get("agents", [])
    agents_dir = PLUGIN_ROOT / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_path = f"./agents/{agent_file.name}"
            if agent_path not in registered_agents:
                result.add_warning("W043", f"Agent not registered: {agent_file.name}")


def run_validation(args) -> ValidationResult:
    """Run all validations based on arguments."""
    result = ValidationResult()

    if args.path:
        path = Path(args.path)

        if args.type == "skill":
            # Handle: SKILL.md file, skill directory, or skills/ parent directory
            if path.is_file() and path.name == "SKILL.md":
                validate_skill(path.parent, result)
            elif path.is_dir() and (path / "SKILL.md").exists():
                validate_skill(path, result)
            elif path.is_dir():
                # Parent directory containing multiple skills
                for skill_dir in path.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                        validate_skill(skill_dir, result)
            else:
                result.add_error("E001", f"Invalid skill path: {path}")

        elif args.type == "agent":
            if path.is_file() and path.name.endswith(".md"):
                validate_agent(path, result)
            elif path.is_dir():
                for agent_file in path.glob("*.md"):
                    validate_agent(agent_file, result)
            else:
                result.add_error("E010", f"Invalid agent path: {path}")

        elif args.type == "command":
            if path.is_file() and path.name.endswith(".md"):
                validate_command(path, result)
            elif path.is_dir():
                for cmd_file in path.glob("*.md"):
                    validate_command(cmd_file, result)
            else:
                result.add_error("E020", f"Invalid command path: {path}")

        elif args.type == "hook":
            if path.is_file() and path.name.endswith(".json"):
                validate_hooks(path, result)
            elif path.is_dir():
                hooks_file = path / "hooks.json"
                if hooks_file.exists():
                    validate_hooks(hooks_file, result)
                else:
                    result.add_error("E030", f"No hooks.json found in: {path}")
            else:
                result.add_error("E030", f"Invalid hook path: {path}")

        # Auto-detect type if not specified
        elif path.is_dir() and (path / "SKILL.md").exists():
            validate_skill(path, result)
        elif path.name.endswith(".md"):
            validate_agent(path, result)
        elif path.name.endswith(".json"):
            validate_hooks(path, result)
    else:
        # Validate all components
        skills_dir = PLUGIN_ROOT / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    validate_skill(skill_dir, result)
        
        agents_dir = PLUGIN_ROOT / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                validate_agent(agent_file, result)
        
        commands_dir = PLUGIN_ROOT / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                validate_command(cmd_file, result)
        
        hooks_file = PLUGIN_ROOT / "hooks" / "hooks.json"
        if hooks_file.exists():
            validate_hooks(hooks_file, result)
        
        # Validate marketplace registration
        validate_marketplace(result)
    
    return result


def print_result(result: ValidationResult, quiet: bool = False):
    """Print validation results."""
    if quiet and result.is_valid():
        return
    
    if result.errors:
        print("\n❌ ERRORS:", file=sys.stderr)
        for code, msg in result.errors:
            print(f"  [{code}] {msg}", file=sys.stderr)
    
    if result.warnings:
        print("\n⚠️  WARNINGS:", file=sys.stderr)
        for code, msg in result.warnings:
            print(f"  [{code}] {msg}", file=sys.stderr)
    
    if result.fixed:
        print("\n🔧 AUTO-FIXED:")
        for fix in result.fixed:
            print(f"  {fix}")
    
    if result.is_valid():
        if not quiet:
            print("\n✅ Validation passed")
    else:
        print(f"\n❌ Validation failed: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")


def main():
    parser = argparse.ArgumentParser(description="Schema validator for assist-plugin")
    parser.add_argument("--path", help="Specific file/directory to validate")
    parser.add_argument("--type", choices=["skill", "agent", "command", "hook"], help="Component type")
    parser.add_argument("--pre-edit", action="store_true", help="Pre-edit validation")
    parser.add_argument("--post-edit", action="store_true", help="Post-edit validation")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--dry-run", action="store_true", help="Show fixes without applying")
    
    args = parser.parse_args()
    
    result = run_validation(args)
    print_result(result, args.quiet)
    
    # Exit code
    if result.is_valid(args.strict):
        sys.exit(0)
    else:
        sys.exit(2)  # BLOCK for PreToolUse hooks


if __name__ == "__main__":
    main()
