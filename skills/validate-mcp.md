---
name: "validate-mcp"
description: "Validate MCP server tools are working correctly"
---

# Skill: Validate MCP

Test MCP (Model Context Protocol) tools for the CorrData server.

## Steps

1. **Check MCP Server Imports**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   python -c "from corrdata.mcp.server_v2 import mcp; print('MCP server imports OK')"
   ```

2. **List Available Tools**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   python -c "
   from corrdata.mcp.server_v2 import mcp
   tools = mcp.list_tools()
   for tool in tools:
       print(f'- {tool.name}: {tool.description[:60]}...')
   "
   ```

3. **Run MCP Tests**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   pytest tests/test_mcp*.py -v --tb=short
   ```

4. **Test Core Tools**
   Use the MCP tools directly to verify:
   - `get_pipeline_summary` returns valid data
   - `search_assets` finds assets
   - `get_asset_status` returns asset details

## Success Criteria

- MCP server imports without errors
- All registered tools are listed
- MCP tests pass
- Core tools return valid responses

## Output Format

```json
{
  "skill": "validate-mcp",
  "status": "pass|fail",
  "tools_registered": 0,
  "tests_passed": 0,
  "tests_failed": 0,
  "errors": []
}
```
