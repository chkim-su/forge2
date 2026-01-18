# MCP Schema Reference

MCP (Model Context Protocol) enables Claude Code to integrate with external tools and services.

## Registration Methods

### Method 1: CLI Registration (Recommended)

```bash
# stdio transport
claude mcp add --transport stdio --scope user <name> -- <command> [args...]

# SSE transport (daemon)
claude mcp add --transport sse --scope user <name> <url>
```

### Method 2: Plugin MCP (via marketplace.json)

```json
{
  "plugins": [{
    "mcpServers": {
      "server-name": {
        "command": "python3",
        "args": ["scripts/mcp-server.py"],
        "env": {}
      }
    }
  }]
}
```

## Transport Types

| Transport | Startup | State Sharing | Use When |
|-----------|---------|---------------|----------|
| **SSE (Daemon)** | 1-2s | ✅ Yes | Default (recommended) |
| **stdio** | 30-60s | ❌ No | Simple, stateless tools |

## Tool Naming Convention

| Registration | Tool Name Pattern |
|--------------|-------------------|
| User MCP | `mcp__<server>__<tool>` |
| Plugin MCP | `mcp__plugin_<plugin>_<server>__<tool>` |

## Daemon Setup (SSE)

```bash
# 1. Start daemon server
python3 scripts/mcp-daemon.py --port 8765 &

# 2. Register with Claude
claude mcp add --transport sse --scope user my-daemon http://127.0.0.1:8765/sse

# 3. Verify
claude mcp list
```

## Schema Fields

### For Plugin MCP (marketplace.json)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "string (required)",
      "args": ["array", "of", "strings"],
      "env": {
        "KEY": "VALUE"
      },
      "cwd": "/optional/working/directory"
    }
  }
}
```

### For CLI Registration

```bash
claude mcp add \
  --transport stdio|sse \
  --scope user|project \
  <name> \
  [-- <command> [args...]]  # For stdio
  [<url>]                    # For sse
```

## Validation Rules

### E050: Invalid transport
```
Error: Transport must be 'stdio' or 'sse'
```

### E051: Missing command (stdio)
```
Error: stdio transport requires command
```

### E052: Missing URL (sse)
```
Error: sse transport requires URL ending with /sse
```

### W050: Non-standard port
```
Warning: SSE URL should use localhost/127.0.0.1 for security
```

## Examples

### Simple stdio MCP

```bash
# Register
claude mcp add --transport stdio --scope user my-tool -- python3 scripts/my-tool.py

# Usage in agent
tools: ["Read", "mcp__my-tool__*"]
```

### SSE Daemon MCP

```bash
# Start daemon
uvx --from git+https://github.com/example/mcp-server \
  mcp-server start --transport sse --port 8765 &

# Register
claude mcp add --transport sse --scope user my-daemon http://127.0.0.1:8765/sse

# Usage
tools: ["Read", "mcp__my-daemon__query", "mcp__my-daemon__execute"]
```

### Plugin MCP (marketplace.json)

```json
{
  "plugins": [{
    "name": "my-plugin",
    "mcpServers": {
      "analyzer": {
        "command": "node",
        "args": ["scripts/analyzer-mcp.js"],
        "env": {
          "LOG_LEVEL": "info"
        }
      }
    }
  }]
}
```

Tool name: `mcp__plugin_my-plugin_analyzer__<tool>`

## Common Patterns

### Pattern 1: Code Analysis MCP

```bash
# Serena for semantic code analysis
uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server --transport sse --port 8765 &

claude mcp add --transport sse --scope user serena http://127.0.0.1:8765/sse
```

### Pattern 2: Database MCP

```json
{
  "mcpServers": {
    "db": {
      "command": "python3",
      "args": ["scripts/db-mcp.py"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Pattern 3: External API Gateway

```bash
# API gateway as SSE daemon
python3 scripts/api-gateway.py --port 8766 &
claude mcp add --transport sse --scope user api http://127.0.0.1:8766/sse
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "MCP not found" | Run `claude mcp list` to verify registration |
| "Connection refused" | Check daemon is running, port is correct |
| "Timeout" | Increase timeout in hooks, check daemon health |
| "Tool not available" | Check agent's `tools:` field includes MCP pattern |
