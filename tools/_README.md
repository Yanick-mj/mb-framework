# Tools

External tool declarations. Each file describes a tool, its permissions, and how to invoke it.

## Format

```markdown
# {Tool Name}

## Description
{What this tool does}

## Access
- **Type**: API | CLI | Webhook | MCP
- **Auth**: {how to authenticate}
- **Env var**: {TOOL_API_KEY}

## Permissions
- **Read**: {what the agent can read}
- **Write**: {what the agent can write}
- **Restrictions**: {what is NOT allowed}

## Usage
{How to invoke — endpoint, CLI command, or MCP tool name}
```

## Adding a Tool

Create a .md file in this directory with the format above.
The orchestrator reads these files to understand what external capabilities are available.
Agents reference tools by name — the orchestrator resolves how to invoke them.
