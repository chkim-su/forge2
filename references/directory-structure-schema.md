# Directory Structure Schema

**Critical rules for Claude Code plugin directory structure**

## Root Level Structure

```
plugin-root/
├── .claude-plugin/           # Plugin metadata (REQUIRED)
│   └── marketplace.json      # Registration file
├── skills/                   # Skill directories
├── agents/                   # Agent files (.md)
├── commands/                 # Command files (.md)
├── hooks/                    # Hook configuration
├── scripts/                  # Executable scripts
├── references/               # Shared documentation
└── README.md                 # Plugin documentation
```

## Critical Rules

### ❌ WRONG: Components inside .claude-plugin/

```
.claude-plugin/
├── commands/      ← WRONG LOCATION
├── agents/        ← WRONG LOCATION
└── skills/        ← WRONG LOCATION
```

### ✅ CORRECT: Components at plugin ROOT

```
plugin-root/
├── .claude-plugin/
│   └── marketplace.json
├── commands/      ← CORRECT
├── agents/        ← CORRECT
└── skills/        ← CORRECT
```

## Component-Specific Rules

### Skills

```
❌ WRONG: Skills as .md files
   skills/my-skill.md

✅ CORRECT: Skills as directories with SKILL.md
   skills/my-skill/
   └── SKILL.md
```

### Commands

```
❌ WRONG: Commands without .md extension
   commands/migrate
   commands/validate

✅ CORRECT: Commands with .md extension
   commands/migrate.md
   commands/validate.md
```

### Agents

```
❌ WRONG: Agents as directories
   agents/my-agent/
   └── agent.md

✅ CORRECT: Agents as single .md files
   agents/my-agent.md
```

### Hooks

```
❌ WRONG: Hook in root
   hooks.json

✅ CORRECT: Hook in hooks/ directory
   hooks/
   └── hooks.json
```

## marketplace.json Schema

```json
{
  "name": "plugin-marketplace-name",
  "description": "Plugin description",
  "version": "1.0.0",
  "owner": {
    "name": "Author Name"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "...",
      "source": "./",
      "version": "1.0.0",
      "skills": [
        "./skills/skill-a",        // Directory path, NO .md
        "./skills/skill-b"
      ],
      "commands": [
        "./commands/cmd-a.md",     // File path WITH .md
        "./commands/cmd-b.md"
      ],
      "agents": [
        "./agents/agent-a.md",     // File path WITH .md
        "./agents/agent-b.md"
      ],
      "hooks": [
        "./hooks/hooks.json"       // JSON file path
      ]
    }
  ]
}
```

## Registration Patterns

### Skills Registration

```json
// ✅ CORRECT
"skills": [
  "./skills/my-skill"
]

// ❌ WRONG
"skills": [
  "./skills/my-skill.md",     // Not a file
  "skills/my-skill",          // Missing ./
  "./skills/my-skill/"        // No trailing slash
]
```

### Commands Registration

```json
// ✅ CORRECT
"commands": [
  "./commands/wizard.md"
]

// ❌ WRONG
"commands": [
  "./commands/wizard",        // Missing .md
  "commands/wizard.md"        // Missing ./
]
```

### Agents Registration

```json
// ✅ CORRECT
"agents": [
  "./agents/analyzer.md"
]

// ❌ WRONG
"agents": [
  "./agents/analyzer",        // Missing .md
  "./agents/analyzer/"        // Not a directory
]
```

## Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Plugin name | kebab-case | `my-awesome-plugin` |
| Skill directory | kebab-case | `skills/code-review/` |
| Agent file | kebab-case | `agents/code-reviewer.md` |
| Command file | kebab-case | `commands/run-tests.md` |
| Script file | kebab-case or snake_case | `scripts/validate_all.py` |

## Validation Errors

| Code | Issue | Fix |
|------|-------|-----|
| E100 | marketplace.json not found | Create .claude-plugin/marketplace.json |
| E101 | Component in wrong location | Move to root level |
| E102 | Skill registered as file | Remove .md from path |
| E103 | Command missing .md | Add .md extension |
| E104 | Agent is directory | Flatten to single file |
