---
name: "generate-dialog"
description: "Generate dialog example demonstrating new capabilities"
---

# Skill: Generate Dialog

Create a dialog example file showing how to use new sprint capabilities.

## When to Use

- Sprint adds new MCP tools
- Sprint adds new GraphQL queries/mutations
- Sprint adds significant new functionality
- Sprint changes user-facing behavior

## Steps

1. **Identify New Capabilities**
   Review sprint file for:
   - New MCP tools added
   - New GraphQL operations
   - New API endpoints
   - New workflows enabled

2. **Create Dialog File**
   Path: `docs/examples/dialog-sprint-{N}-{feature}.md`

   Template:
   ```markdown
   # Dialog Example: {Feature Name}

   Sprint: {N}
   Created: {date}

   ## Scenario
   {Brief description of what the user is trying to accomplish}

   ## Dialog

   **User**: {Natural language request}

   **Assistant**: {Response explaining what will be done}

   **Tool Call**: {Tool name and parameters}

   **Result**: {Summary of tool output}

   **Assistant**: {Interpretation and next steps}

   ## Key Capabilities Demonstrated
   - {Capability 1}
   - {Capability 2}
   ```

3. **Validate Dialog**
   - Ensure tool calls match actual tool signatures
   - Verify responses are accurate
   - Test the workflow manually if possible

## Success Criteria

- Dialog file created in correct location
- Dialog demonstrates primary new capability
- Tool calls are syntactically correct
- Response flow is realistic

## Output Format

```json
{
  "skill": "generate-dialog",
  "status": "pass|fail",
  "dialog_path": "",
  "capabilities_documented": []
}
```
