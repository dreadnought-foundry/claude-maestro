# Recipe: MCP Tool Registry Pattern

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Multiple (foundation pattern)
**ADRs**: [ADR-006](../../architecture/decisions/ADR-006-mcp-server-llm-integration.md), [ADR-024](../../architecture/decisions/ADR-024-modular-mcp-architecture.md), [ADR-034](../../architecture/decisions/ADR-034-mcp-tool-registry.md)

## Context

**When to use this recipe:**
- Building Model Context Protocol (MCP) servers for LLM integration
- Exposing 10+ tools with consistent parameter schemas
- Supporting auto-generated JSON Schema for tool definitions
- Creating modular, testable tool architectures
- Enabling tools to be registered dynamically from modules

**When NOT to use this recipe:**
- Simple one-off LLM integrations with <5 tools
- When tools have radically different patterns (no commonality)
- Prototyping where schema flexibility is more important than consistency
- When JSON Schema generation isn't needed

## Ingredients

Before starting, ensure you have:

- [ ] MCP SDK installed (`mcp` package)
- [ ] Understanding of JSON Schema specification
- [ ] Python dataclasses knowledge
- [ ] Async/await programming experience
- [ ] Clear list of tools and their parameters
- [ ] Test suite for tool validation

## Overview

The Tool Registry pattern separates tool definition (schema) from implementation (handler):

```
┌─────────────────────────────────────────────────────────────────┐
│                         LLM CLIENT                               │
│  (Claude Desktop, Cline, etc.)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    MCP list_tools request
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      TOOL REGISTRY                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ToolDefinition → JSON Schema                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ParamDefinition → Parameter Schema                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    call_tool request
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    TOOL HANDLERS                                 │
│  (Async functions that implement tool logic)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Steps

### Step 1: Define Parameter Building Blocks

Create dataclass for parameter definitions:

```python
# src/corrdata/mcp/tools/base.py
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ParamDefinition:
    """
    Definition of a single tool parameter.
    Converts to JSON Schema format.
    """
    name: str
    type: str  # "string", "integer", "number", "boolean", "array", "object"
    description: str = ""
    required: bool = False
    default: Any = None

    # Validation constraints
    enum: Optional[list[str]] = None
    minimum: Optional[int | float] = None
    maximum: Optional[int | float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    # For array types
    items_type: Optional[str] = None  # Type of array items
    items_enum: Optional[list[str]] = None  # Enum for array items

    # For object types
    properties: Optional[dict[str, "ParamDefinition"]] = None

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {"type": self.type}

        if self.description:
            schema["description"] = self.description

        if self.enum:
            schema["enum"] = self.enum

        if self.minimum is not None:
            schema["minimum"] = self.minimum

        if self.maximum is not None:
            schema["maximum"] = self.maximum

        if self.min_length is not None:
            schema["minLength"] = self.min_length

        if self.max_length is not None:
            schema["maxLength"] = self.max_length

        if self.pattern:
            schema["pattern"] = self.pattern

        # Array type
        if self.type == "array":
            if self.items_type:
                items_schema = {"type": self.items_type}
                if self.items_enum:
                    items_schema["enum"] = self.items_enum
                schema["items"] = items_schema

        # Object type
        if self.type == "object" and self.properties:
            schema["properties"] = {
                name: param.to_schema()
                for name, param in self.properties.items()
            }

        return schema
```

**Expected outcome**: Reusable parameter definition that generates JSON Schema.

### Step 2: Create Parameter Factory

Build factory class with common parameter patterns:

```python
# src/corrdata/mcp/tools/params.py
from corrdata.mcp.tools.base import ParamDefinition

class Param:
    """
    Factory class for creating common parameter definitions.
    Provides type-safe helpers for standard patterns.
    """

    @staticmethod
    def string(
        name: str,
        description: str = "",
        required: bool = False,
        default: Optional[str] = None,
        enum: Optional[list[str]] = None,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> ParamDefinition:
        """Create string parameter."""
        return ParamDefinition(
            name=name,
            type="string",
            description=description,
            required=required,
            default=default,
            enum=enum,
            pattern=pattern,
            min_length=min_length,
            max_length=max_length,
        )

    @staticmethod
    def integer(
        name: str,
        description: str = "",
        required: bool = False,
        default: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
    ) -> ParamDefinition:
        """Create integer parameter."""
        return ParamDefinition(
            name=name,
            type="integer",
            description=description,
            required=required,
            default=default,
            minimum=minimum,
            maximum=maximum,
        )

    @staticmethod
    def number(
        name: str,
        description: str = "",
        required: bool = False,
        default: Optional[float] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ) -> ParamDefinition:
        """Create number (float) parameter."""
        return ParamDefinition(
            name=name,
            type="number",
            description=description,
            required=required,
            default=default,
            minimum=minimum,
            maximum=maximum,
        )

    @staticmethod
    def boolean(
        name: str,
        description: str = "",
        required: bool = False,
        default: Optional[bool] = None,
    ) -> ParamDefinition:
        """Create boolean parameter."""
        return ParamDefinition(
            name=name,
            type="boolean",
            description=description,
            required=required,
            default=default,
        )

    @staticmethod
    def enum(
        name: str,
        values: list[str],
        description: str = "",
        required: bool = False,
        default: Optional[str] = None,
    ) -> ParamDefinition:
        """Create enum parameter (string with allowed values)."""
        return ParamDefinition(
            name=name,
            type="string",
            description=description,
            required=required,
            default=default,
            enum=values,
        )

    @staticmethod
    def array(
        name: str,
        items_type: str = "string",
        items_enum: Optional[list[str]] = None,
        description: str = "",
        required: bool = False,
    ) -> ParamDefinition:
        """Create array parameter."""
        return ParamDefinition(
            name=name,
            type="array",
            description=description,
            required=required,
            items_type=items_type,
            items_enum=items_enum,
        )

    # Domain-specific helpers for CorrData

    @staticmethod
    def asset_uuid(required: bool = True) -> ParamDefinition:
        """Standard asset UUID parameter."""
        return Param.string(
            "asset_uuid",
            description="UUID of the asset (segment, test station, rectifier, etc.)",
            required=required,
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )

    @staticmethod
    def limit(default: int = 100, maximum: int = 1000) -> ParamDefinition:
        """Standard limit parameter for paginated results."""
        return Param.integer(
            "limit",
            description="Maximum number of results to return",
            required=False,
            default=default,
            minimum=1,
            maximum=maximum,
        )

    @staticmethod
    def date_range() -> list[ParamDefinition]:
        """Standard date range parameters (start_date, end_date)."""
        return [
            Param.string(
                "start_date",
                description="Start date in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')",
                required=False,
                pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
            ),
            Param.string(
                "end_date",
                description="End date in ISO 8601 format",
                required=False,
                pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
            ),
        ]

    @staticmethod
    def measurement_type() -> ParamDefinition:
        """Standard measurement type parameter."""
        return Param.enum(
            "measurement_type",
            values=[
                "pipe_to_soil_potential",
                "rectifier_voltage",
                "rectifier_current",
                "soil_resistivity",
                "coating_condition",
            ],
            description="Type of measurement",
            required=False,
        )

    @staticmethod
    def asset_type() -> ParamDefinition:
        """Standard asset type parameter."""
        return Param.enum(
            "asset_type",
            values=["segment", "test_station", "rectifier", "bond", "anode_bed"],
            description="Type of pipeline asset",
            required=False,
        )
```

**Expected outcome**: Reusable parameter factory with domain-specific helpers.

### Step 3: Define Tool Definition

Create tool definition dataclass:

```python
# src/corrdata/mcp/tools/base.py (continued)
from mcp.types import Tool

@dataclass
class ToolDefinition:
    """
    Complete definition of an MCP tool.
    Separates interface (schema) from implementation (handler).
    """
    name: str
    description: str
    parameters: list[ParamDefinition] = field(default_factory=list)

    def to_mcp_tool(self) -> Tool:
        """
        Convert to MCP Tool format.
        Generates JSON Schema from parameter definitions.
        """
        # Build properties dict
        properties = {
            param.name: param.to_schema()
            for param in self.parameters
        }

        # Extract required parameters
        required = [
            param.name
            for param in self.parameters
            if param.required
        ]

        # Build input schema
        input_schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            input_schema["required"] = required

        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=input_schema
        )

    def validate_arguments(self, arguments: dict) -> list[str]:
        """
        Validate arguments against parameter definitions.
        Returns list of error messages (empty if valid).
        """
        errors = []

        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in arguments:
                errors.append(f"Missing required parameter: {param.name}")

        # Check parameter types and constraints
        for param in self.parameters:
            if param.name not in arguments:
                continue

            value = arguments[param.name]

            # Type validation
            if param.type == "integer" and not isinstance(value, int):
                errors.append(f"{param.name} must be an integer")
            elif param.type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{param.name} must be a number")
            elif param.type == "string" and not isinstance(value, str):
                errors.append(f"{param.name} must be a string")
            elif param.type == "boolean" and not isinstance(value, bool):
                errors.append(f"{param.name} must be a boolean")

            # Range validation
            if param.minimum is not None and value < param.minimum:
                errors.append(f"{param.name} must be >= {param.minimum}")
            if param.maximum is not None and value > param.maximum:
                errors.append(f"{param.name} must be <= {param.maximum}")

            # Enum validation
            if param.enum and value not in param.enum:
                errors.append(f"{param.name} must be one of: {param.enum}")

        return errors
```

**Expected outcome**: Tool definition that generates MCP Tool with JSON Schema.

### Step 4: Implement Tool Registry

Create registry for registering and dispatching tools:

```python
# src/corrdata/mcp/tools/registry.py
from typing import Callable, Awaitable
from collections.abc import Sequence
from mcp.types import Tool, TextContent
from corrdata.mcp.tools.base import ToolDefinition

ToolHandler = Callable[[dict], Awaitable[Sequence[TextContent]]]

class ToolRegistry:
    """
    Registry for MCP tools.
    Provides centralized tool management and dispatching.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(
        self,
        definition: ToolDefinition,
        handler: ToolHandler
    ) -> None:
        """
        Register a tool definition with its handler.

        Args:
            definition: Tool schema definition
            handler: Async function that implements the tool
        """
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def list_tools(self) -> list[Tool]:
        """
        Get all registered tools in MCP format.
        Called by MCP server to respond to list_tools request.
        """
        return [tool.to_mcp_tool() for tool in self._tools.values()]

    async def dispatch(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[TextContent]:
        """
        Dispatch a tool call to its handler.

        Args:
            name: Tool name
            arguments: Tool arguments from LLM

        Returns:
            Tool response as TextContent

        Raises:
            ValueError: If tool not found or arguments invalid
        """
        # Check tool exists
        if name not in self._tools:
            raise ValueError(
                f"Unknown tool: {name}. "
                f"Available tools: {list(self._tools.keys())}"
            )

        definition = self._tools[name]
        handler = self._handlers[name]

        # Validate arguments
        errors = definition.validate_arguments(arguments)
        if errors:
            error_msg = "Invalid arguments:\n" + "\n".join(f"- {e}" for e in errors)
            return [TextContent(type="text", text=error_msg)]

        # Execute handler
        try:
            return await handler(arguments)
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    def get_tool(self, name: str) -> ToolDefinition:
        """Get tool definition by name."""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name]

    def tool_count(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

# Global registry instance
registry = ToolRegistry()
```

**Expected outcome**: Centralized registry for all MCP tools.

### Step 5: Define and Register a Tool

Create tool definition and handler, then register:

```python
# src/corrdata/mcp/tools/asset_tools.py
import json
from typing import Sequence
from uuid import UUID
from mcp.types import TextContent
from corrdata.mcp.tools.base import ToolDefinition
from corrdata.mcp.tools.params import Param
from corrdata.mcp.tools.registry import registry
from corrdata.db.session import async_session
from corrdata.db.models import Asset
from sqlalchemy import select

# Define tool schema
get_asset_status = ToolDefinition(
    name="get_asset_status",
    description=(
        "Get current status of a pipeline asset including recent measurements, "
        "events, and risk score. Use this to check on segment health, "
        "test station readings, or rectifier performance."
    ),
    parameters=[
        Param.asset_uuid(required=True),
        Param.boolean(
            "include_measurements",
            description="Include recent measurements in response",
            default=True
        ),
        Param.boolean(
            "include_events",
            description="Include recent events in response",
            default=True
        ),
        Param.integer(
            "measurement_limit",
            description="Number of recent measurements to include",
            default=10,
            minimum=1,
            maximum=100
        ),
    ]
)

# Define handler
async def handle_get_asset_status(arguments: dict) -> Sequence[TextContent]:
    """
    Handler for get_asset_status tool.
    Fetches asset data and formats response for LLM.
    """
    asset_uuid = UUID(arguments["asset_uuid"])
    include_measurements = arguments.get("include_measurements", True)
    include_events = arguments.get("include_events", True)
    measurement_limit = arguments.get("measurement_limit", 10)

    async with async_session() as session:
        # Fetch asset
        stmt = select(Asset).where(Asset.uuid == asset_uuid)
        result = await session.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            return [TextContent(
                type="text",
                text=f"Asset not found: {asset_uuid}"
            )]

        # Build response
        response = {
            "asset": {
                "uuid": str(asset.uuid),
                "name": asset.name,
                "type": asset.asset_type,
                "status": asset.status,
                "risk_score": calculate_risk_score(asset),  # Placeholder
            }
        }

        # Add measurements if requested
        if include_measurements:
            measurements = await get_recent_measurements(
                session,
                asset_uuid,
                limit=measurement_limit
            )
            response["measurements"] = [
                {
                    "type": m.measurement_type,
                    "value": float(m.value),
                    "unit": m.unit,
                    "timestamp": m.recorded_at.isoformat(),
                }
                for m in measurements
            ]

        # Add events if requested
        if include_events:
            events = await get_recent_events(session, asset_uuid)
            response["events"] = [
                {
                    "type": e.event_type,
                    "severity": e.severity,
                    "description": e.description,
                    "timestamp": e.created_at.isoformat(),
                }
                for e in events
            ]

        # Format as text for LLM
        text = f"Asset Status for {asset.name} ({asset.asset_type})\n\n"
        text += f"Status: {asset.status}\n"
        text += f"Risk Score: {response['asset']['risk_score']}/100\n\n"

        if include_measurements and response.get("measurements"):
            text += "Recent Measurements:\n"
            for m in response["measurements"][:5]:  # Show top 5
                text += f"- {m['type']}: {m['value']} {m['unit']} at {m['timestamp']}\n"

        if include_events and response.get("events"):
            text += "\nRecent Events:\n"
            for e in response["events"][:5]:
                text += f"- {e['severity']}: {e['description']} at {e['timestamp']}\n"

        # Return both formatted text and raw JSON
        return [
            TextContent(type="text", text=text),
            TextContent(
                type="text",
                text=f"\n\nRaw JSON:\n{json.dumps(response, indent=2)}"
            ),
        ]

# Register tool
registry.register(get_asset_status, handle_get_asset_status)
```

**Expected outcome**: Complete tool with schema and handler, registered in global registry.

### Step 6: Integrate with MCP Server

Use registry in MCP server:

```python
# src/corrdata/mcp/server_v2.py
from mcp.server import Server
from mcp.types import TextContent
from corrdata.mcp.tools.registry import registry

# Import all tool modules to register them
from corrdata.mcp.tools import asset_tools, measurement_tools, alert_tools

# Create MCP server
server = Server("corrdata-mcp")

@server.list_tools()
async def list_tools():
    """Return all registered tools."""
    return registry.list_tools()

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Dispatch tool call to registry."""
    return await registry.dispatch(name, arguments)

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

**Expected outcome**: MCP server that uses registry for tool management.

## Code Examples

### Testing Tool Definition

```python
# tests/test_mcp_tools.py
import pytest
from corrdata.mcp.tools.registry import registry
from corrdata.mcp.tools.asset_tools import get_asset_status

def test_tool_registration():
    """Test that tool is properly registered."""
    tool = registry.get_tool("get_asset_status")
    assert tool.name == "get_asset_status"
    assert len(tool.parameters) == 4

def test_tool_json_schema():
    """Test that tool generates valid JSON Schema."""
    mcp_tool = get_asset_status.to_mcp_tool()

    assert mcp_tool.name == "get_asset_status"
    assert "asset_uuid" in mcp_tool.inputSchema["properties"]
    assert "asset_uuid" in mcp_tool.inputSchema["required"]

def test_argument_validation():
    """Test that invalid arguments are rejected."""
    # Missing required parameter
    errors = get_asset_status.validate_arguments({})
    assert len(errors) > 0
    assert "asset_uuid" in errors[0]

    # Invalid type
    errors = get_asset_status.validate_arguments({
        "asset_uuid": "not-a-uuid",
        "measurement_limit": "not-an-integer"  # Should be int
    })
    assert len(errors) > 0

    # Valid arguments
    errors = get_asset_status.validate_arguments({
        "asset_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "include_measurements": True,
        "measurement_limit": 10
    })
    assert len(errors) == 0

@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool handler execution."""
    result = await registry.dispatch(
        "get_asset_status",
        {
            "asset_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "include_measurements": True,
        }
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert isinstance(result[0], TextContent)
```

### Batch Tool Registration

```python
# src/corrdata/mcp/tools/__init__.py
from corrdata.mcp.tools.registry import registry
from corrdata.mcp.tools.base import ToolDefinition
from corrdata.mcp.tools.params import Param

def register_measurement_tools():
    """Register all measurement-related tools."""

    tools = [
        (
            ToolDefinition(
                name="get_measurements",
                description="Get measurements for an asset",
                parameters=[Param.asset_uuid(), *Param.date_range()],
            ),
            handle_get_measurements
        ),
        (
            ToolDefinition(
                name="record_measurement",
                description="Record a new field measurement",
                parameters=[
                    Param.asset_uuid(),
                    Param.measurement_type(),
                    Param.number("value", "Measurement value", required=True),
                ],
            ),
            handle_record_measurement
        ),
    ]

    for definition, handler in tools:
        registry.register(definition, handler)
```

## Learnings

### From Multiple Sprints

- **Validation saves debugging time**: Validate arguments in registry before calling handler
- **JSON Schema generation**: Automated schema generation ensures consistency
- **Domain-specific helpers**: `Param.asset_uuid()` and similar reduce duplication
- **Separation of concerns**: Tool definition independent of implementation enables testing
- **Error messages matter**: Return clear error messages for LLM to understand

### Performance Insights

- Registry lookup is O(1) - scales to 100+ tools
- JSON Schema generation is cached per tool
- Argument validation adds <1ms overhead

## Anti-Patterns

### Don't: Define Schema in Handler

**What it looks like**:
```python
# Bad - schema embedded in handler
async def handle_tool(arguments):
    if "asset_uuid" not in arguments:
        raise ValueError("Missing asset_uuid")
    # ... logic
```

**Why it's bad**: No schema for LLM, validation scattered, not testable.

**Instead**: Use ToolDefinition with explicit parameters.

### Don't: Skip Argument Validation

**What it looks like**:
```python
# Bad - no validation
async def dispatch(name, arguments):
    return await self._handlers[name](arguments)  # Assumes valid
```

**Why it's bad**: Invalid arguments crash handler, poor error messages.

**Instead**: Validate with `definition.validate_arguments()` before calling handler.

### Don't: Return Unstructured Errors

**What it looks like**:
```python
# Bad - raises exception
async def handle_tool(arguments):
    raise ValueError("Something went wrong")
```

**Why it's bad**: LLM gets raw exception, can't handle gracefully.

**Instead**: Return TextContent with clear error message.

## Variations

### For Tools with Complex Object Parameters

```python
# Define nested object schema
location_param = ParamDefinition(
    name="location",
    type="object",
    description="Geographic location",
    properties={
        "latitude": Param.number("latitude", required=True, minimum=-90, maximum=90),
        "longitude": Param.number("longitude", required=True, minimum=-180, maximum=180),
    }
)
```

### For Tools with Optional Array Parameters

```python
Param.array(
    "asset_uuids",
    items_type="string",
    description="List of asset UUIDs to query",
    required=False
)
```

### For Tools with Contextual Validation

```python
class ToolDefinition:
    def validate_arguments_with_context(
        self,
        arguments: dict,
        context: dict
    ) -> list[str]:
        """Validate arguments with additional context (e.g., user permissions)."""
        errors = self.validate_arguments(arguments)

        # Additional contextual validation
        if "tenant_id" in context:
            # Check asset belongs to tenant
            pass

        return errors
```

## Related Recipes

- [Provider Pattern](./provider-pattern.md) - Exposing providers as MCP tools
- [GraphQL Schema Design](./graphql-schema.md) - Similar schema definition patterns
- [Domain Model Layering](./domain-model-layering.md) - Converting data for tool responses

## Verification

### List All Registered Tools

```python
from corrdata.mcp.tools.registry import registry

tools = registry.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
    print(f"  Parameters: {list(tool.inputSchema['properties'].keys())}")
```

### Validate Tool Schema

```bash
# Generate JSON Schema and validate against JSON Schema spec
python -c "
from corrdata.mcp.tools.registry import registry
import json

tools = registry.list_tools()
schema = {
    'tools': [
        {
            'name': t.name,
            'inputSchema': t.inputSchema
        }
        for t in tools
    ]
}
print(json.dumps(schema, indent=2))
" | jsonschema validate
```

### Test Tool in MCP Inspector

```bash
# Start MCP server
python -m corrdata.mcp.server_v2

# In Claude Desktop, add MCP server config
# Test tool call:
# "Get status for asset 123e4567-e89b-12d3-a456-426614174000"
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on ADR-006, ADR-024, ADR-034 |
