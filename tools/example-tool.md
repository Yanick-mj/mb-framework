# Example: Make (Automation)

## Description
Workflow automation platform for connecting apps and services.

## Access
- **Type**: API + Webhook
- **Auth**: API key in header
- **Env var**: `MAKE_API_KEY`

## Permissions
- **Read**: Scenario status, execution logs
- **Write**: Trigger scenarios, create/update scenarios
- **Restrictions**: Cannot delete organization-level settings

## Usage
```
POST https://hook.make.com/{webhook_id}
Content-Type: application/json
Authorization: Bearer $MAKE_API_KEY

{ "data": "..." }
```

## When to Use
- Automate repetitive workflows
- Connect external services (email, Slack, CRM)
- Trigger actions on events
