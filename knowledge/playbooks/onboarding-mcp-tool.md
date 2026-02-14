# Playbook: Onboarding a New MCP Tool Module

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2025-12-14
**Estimated Time**: 1-2 hours
**Prerequisites**:
- Understanding of MCP (Model Context Protocol)
- Familiarity with async Python and FastAPI
- Knowledge of the ToolRegistry pattern
- Database models understanding (if tool queries data)

**Related Patterns**:
- [MCP Tool Registry (ADR-034)](../../architecture/decisions/ADR-034-mcp-tool-registry.md)
- [Modular MCP Architecture (ADR-024)](../../architecture/decisions/ADR-024-modular-mcp-architecture.md)
- [MCP Server LLM Integration (ADR-006)](../../architecture/decisions/ADR-006-mcp-server-llm-integration.md)

## Overview

This playbook guides you through creating and registering a new MCP tool module in CorrData's modular MCP server architecture. MCP tools provide structured interfaces for LLMs to query data, perform calculations, and execute domain-specific operations.

The modular architecture organizes tools by domain (core, predictive, compliance, etc.) and uses lazy loading to minimize context usage. Each module is self-contained with its own registry and handlers.

## When to Use This Playbook

- You need to add new LLM-accessible functionality
- You're implementing a new domain area (e.g., new compliance requirement)
- You want to expose database queries or calculations to LLMs
- You're adding tools for a specific workflow (e.g., audit workflow, field operations)
- You need to extend existing tool modules with new capabilities

## Checklist

- [ ] Step 1: Determine domain/module for tool
- [ ] Step 2: Create ToolDefinition with parameters
- [ ] Step 3: Implement async handler function
- [ ] Step 4: Register tool with module registry
- [ ] Step 5: Update server_v2.py module imports
- [ ] Step 6: Write comprehensive tests
- [ ] Step 7: Verify tool appears in list_tools()
- [ ] Step 8: Document usage and examples

## Step 1: Determine Domain/Module for Tool

### What You'll Do
Analyze your tool's purpose and determine which existing module it belongs to, or whether you need to create a new module.

### Instructions

1. Review existing modules in `src/corrdata/mcp/tools/`
2. Identify the domain area for your tool
3. Check if an appropriate module already exists
4. If creating new module, plan its scope

### Existing Modules (as of Sprint 103)

| Module | Purpose | Example Tools |
|--------|---------|---------------|
| core | Asset queries, measurements, search | get_asset_status, query_measurements |
| predictive | Corrosion prediction, risk analysis | predict_corrosion, explain_risk |
| external | External factors (soil, coating, etc.) | get_soil_chemistry, get_coating_condition |
| alerts | Alert management | create_alert, get_active_alerts |
| compliance | Regulatory compliance | get_compliance_status, generate_annual_report |
| calendar | Compliance calendar & submissions | get_upcoming_deadlines, track_submission |
| mobile | Field operations | get_work_orders, create_field_reading |
| geospatial | Terrain, flood zones | get_elevation_profile, analyze_flood_risk |

### Example Decision Process

**Scenario**: You need to add tools for managing compliance audits.

**Analysis**:
- Purpose: Track and manage regulatory audits
- Related to: Compliance domain
- Existing module: `compliance.py` exists
- Decision: Add to existing `compliance` module

**Alternative Scenario**: You need tools for a complex audit workflow (create audit, assign auditors, track findings, generate reports).

**Analysis**:
- Purpose: Full audit lifecycle management
- Related to: Compliance, but substantial scope
- Existing module: `compliance.py` has general compliance tools
- Decision: Create new `audit.py` module for focused audit workflow

### Files to Review
- `src/corrdata/mcp/tools/` (list existing modules)
- `src/corrdata/mcp/server_v2.py` (see registered modules)

### Verification
- Module domain is clearly defined
- No overlap with existing modules
- Scope is appropriate (not too narrow, not too broad)

## Step 2: Create ToolDefinition with Parameters

### What You'll Do
Define your tool using ToolDefinition and Param classes. This creates the structured schema that LLMs use to understand how to call your tool.

### Files to Create/Modify
- `src/corrdata/mcp/tools/compliance.py` (example: adding to existing module)

### Code

Let's add a tool for creating and tracking compliance audits:

```python
# Add to src/corrdata/mcp/tools/compliance.py

from corrdata.mcp.tools import Param, ToolDefinition, ToolRegistry

# Create module-level registry (if not already exists)
registry = ToolRegistry()

# =============================================================================
# New Tool Definition
# =============================================================================

create_audit_tool = ToolDefinition(
    name="create_compliance_audit",
    description=(
        "Create a new compliance audit record. "
        "Captures audit type, scope, schedule, and assigns auditors. "
        "Returns audit ID and tracking information."
    ),
    parameters=[
        Param.enum(
            name="audit_type",
            values=[
                "internal",
                "external",
                "phmsa",
                "state_regulatory",
                "third_party"
            ],
            description="Type of audit being conducted",
            required=True,
        ),
        Param.string(
            name="audit_name",
            description="Descriptive name for the audit",
            required=True,
        ),
        Param.enum(
            name="scope",
            values=[
                "integrity_management",
                "ops_maintenance",
                "drug_alcohol",
                "operator_qualification",
                "public_awareness",
                "damage_prevention",
                "full_compliance"
            ],
            description="Scope of the audit",
            required=True,
        ),
        Param.string(
            name="start_date",
            description="Audit start date (ISO 8601 format: YYYY-MM-DD)",
            required=True,
        ),
        Param.string(
            name="end_date",
            description="Audit end date (ISO 8601 format: YYYY-MM-DD)",
            required=True,
        ),
        Param.array(
            name="auditor_ids",
            items_type="string",
            description="List of auditor employee IDs assigned to this audit",
        ),
        Param.string(
            name="lead_auditor_id",
            description="Employee ID of the lead auditor",
        ),
        Param.array(
            name="regulation_ids",
            items_type="string",
            description="List of regulation IDs being audited (e.g., '192.903', '195.573')",
        ),
        Param.string(
            name="description",
            description="Detailed description of audit objectives and requirements",
        ),
        Param.enum(
            name="priority",
            values=["low", "medium", "high", "critical"],
            description="Priority level of the audit",
            default="medium",
        ),
    ],
)

get_audit_status_tool = ToolDefinition(
    name="get_audit_status",
    description=(
        "Get status and details of a compliance audit. "
        "Returns findings, progress, assigned auditors, and completion status."
    ),
    parameters=[
        Param.string(
            name="audit_id",
            description="Unique identifier of the audit (UUID or audit number)",
            required=True,
        ),
        Param.boolean(
            name="include_findings",
            description="Include detailed findings in response (default: true)",
            default=True,
        ),
    ],
)

list_audits_tool = ToolDefinition(
    name="list_compliance_audits",
    description=(
        "List compliance audits with optional filtering. "
        "Returns summary of audits matching criteria."
    ),
    parameters=[
        Param.enum(
            name="status",
            values=["planned", "in_progress", "review", "completed", "archived"],
            description="Filter by audit status",
        ),
        Param.enum(
            name="audit_type",
            values=["internal", "external", "phmsa", "state_regulatory", "third_party"],
            description="Filter by audit type",
        ),
        Param.string(
            name="start_date",
            description="Filter audits starting on or after this date (ISO 8601)",
        ),
        Param.string(
            name="end_date",
            description="Filter audits ending on or before this date (ISO 8601)",
        ),
        Param.limit(default=20),
    ],
)
```

### Parameter Best Practices

**Use the Param factory methods**:
- `Param.string()` - Text fields, IDs, descriptions
- `Param.integer()` - Counts, limits, numeric IDs
- `Param.number()` - Float values (measurements, percentages)
- `Param.boolean()` - Flags and options
- `Param.enum()` - Constrained choices (audit types, statuses)
- `Param.array()` - Lists of items (auditor IDs, regulation IDs)
- `Param.object()` - Complex nested data

**Use standard helper parameters**:
- `Param.asset_uuid()` - For asset references
- `Param.segment_uuid()` - For segment references
- `Param.limit()` - For pagination (auto-constrains 1-1000)
- `Param.date_range()` - Returns tuple of start_time/end_time params
- `Param.priority()` - Standard priority enum

### Verification
```python
# Test tool definition
python3 -c "
from corrdata.mcp.tools.compliance import create_audit_tool

mcp_tool = create_audit_tool.to_mcp_tool()
print('Tool name:', mcp_tool.name)
print('Parameters:', list(mcp_tool.inputSchema['properties'].keys()))
print('Required:', mcp_tool.inputSchema.get('required', []))
"
```

## Step 3: Implement Async Handler Function

### What You'll Do
Write the async handler function that executes when the tool is called. This function receives arguments and returns results to the LLM.

### Files to Modify
- Same file as Step 2 (`src/corrdata/mcp/tools/compliance.py`)

### Code

```python
# Add to src/corrdata/mcp/tools/compliance.py

from datetime import date, datetime
from typing import Any
from uuid import uuid4

from mcp.types import TextContent
from sqlalchemy import select

from corrdata.db.models import ComplianceAudit, Regulation  # Example models
from corrdata.db.session import async_session_factory
from corrdata.mcp.tools.base import error_response, json_response, validate_uuid


# =============================================================================
# Handler Implementations
# =============================================================================

async def handle_create_audit(args: dict[str, Any]) -> list[TextContent]:
    """Create a new compliance audit.

    Args:
        args: Tool arguments containing audit details

    Returns:
        JSON response with created audit information
    """
    # Extract and validate arguments
    audit_type = args.get("audit_type")
    audit_name = args.get("audit_name")
    scope = args.get("scope")
    start_date_str = args.get("start_date")
    end_date_str = args.get("end_date")
    auditor_ids = args.get("auditor_ids", [])
    lead_auditor_id = args.get("lead_auditor_id")
    regulation_ids = args.get("regulation_ids", [])
    description = args.get("description")
    priority = args.get("priority", "medium")

    # Validate required fields
    if not audit_type or not audit_name or not scope:
        return error_response("audit_type, audit_name, and scope are required")

    # Parse and validate dates
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        if end_date < start_date:
            return error_response("end_date must be after start_date")

    except (ValueError, TypeError) as e:
        return error_response(f"Invalid date format: {e}")

    # Create audit record
    audit_id = uuid4()
    audit_number = f"AUDIT-{datetime.now().strftime('%Y%m%d')}-{audit_id.hex[:6].upper()}"

    async with async_session_factory() as session:
        # Verify regulations exist (if provided)
        if regulation_ids:
            result = await session.execute(
                select(Regulation).where(Regulation.regulation_id.in_(regulation_ids))
            )
            found_regs = {r.regulation_id for r in result.scalars().all()}
            missing_regs = set(regulation_ids) - found_regs

            if missing_regs:
                return error_response(
                    f"Unknown regulation IDs: {', '.join(missing_regs)}"
                )

        # Create audit
        audit = ComplianceAudit(
            uuid=audit_id,
            audit_number=audit_number,
            audit_type=audit_type,
            audit_name=audit_name,
            scope=scope,
            start_date=start_date,
            end_date=end_date,
            auditor_ids=auditor_ids,
            lead_auditor_id=lead_auditor_id,
            regulation_ids=regulation_ids,
            description=description,
            priority=priority,
            status="planned",
            created_at=datetime.now(),
        )

        session.add(audit)
        await session.commit()
        await session.refresh(audit)

    result = {
        "audit_id": str(audit.uuid),
        "audit_number": audit.audit_number,
        "audit_type": audit.audit_type,
        "audit_name": audit.audit_name,
        "scope": audit.scope,
        "start_date": audit.start_date.isoformat(),
        "end_date": audit.end_date.isoformat(),
        "status": audit.status,
        "priority": audit.priority,
        "auditor_count": len(auditor_ids),
        "regulation_count": len(regulation_ids),
        "message": f"Audit {audit_number} created successfully",
    }

    return json_response(result)


async def handle_get_audit_status(args: dict[str, Any]) -> list[TextContent]:
    """Get audit status and details.

    Args:
        args: Tool arguments containing audit_id and options

    Returns:
        JSON response with audit details
    """
    audit_id_str = args.get("audit_id")
    include_findings = args.get("include_findings", True)

    if not audit_id_str:
        return error_response("audit_id is required")

    # Validate UUID
    audit_uuid = validate_uuid(audit_id_str)
    if audit_uuid is None:
        # Try as audit number instead
        audit_query_field = ComplianceAudit.audit_number
        audit_query_value = audit_id_str
    else:
        audit_query_field = ComplianceAudit.uuid
        audit_query_value = audit_uuid

    async with async_session_factory() as session:
        result = await session.execute(
            select(ComplianceAudit).where(audit_query_field == audit_query_value)
        )
        audit = result.scalar_one_or_none()

        if not audit:
            return error_response(f"Audit not found: {audit_id_str}")

        # Build response
        response = {
            "audit_id": str(audit.uuid),
            "audit_number": audit.audit_number,
            "audit_type": audit.audit_type,
            "audit_name": audit.audit_name,
            "scope": audit.scope,
            "status": audit.status,
            "priority": audit.priority,
            "start_date": audit.start_date.isoformat(),
            "end_date": audit.end_date.isoformat(),
            "lead_auditor_id": audit.lead_auditor_id,
            "auditor_ids": audit.auditor_ids,
            "regulation_ids": audit.regulation_ids,
            "description": audit.description,
            "progress": {
                "days_until_start": (audit.start_date - date.today()).days,
                "days_remaining": (audit.end_date - date.today()).days,
                "completion_percentage": audit.completion_percentage or 0,
            },
        }

        # Include findings if requested
        if include_findings and hasattr(audit, "findings"):
            response["findings"] = [
                {
                    "id": str(f.uuid),
                    "severity": f.severity,
                    "regulation_id": f.regulation_id,
                    "description": f.description,
                    "status": f.status,
                }
                for f in audit.findings
            ]
            response["findings_summary"] = {
                "total": len(audit.findings),
                "critical": sum(1 for f in audit.findings if f.severity == "critical"),
                "high": sum(1 for f in audit.findings if f.severity == "high"),
                "medium": sum(1 for f in audit.findings if f.severity == "medium"),
                "low": sum(1 for f in audit.findings if f.severity == "low"),
            }

    return json_response(response)


async def handle_list_audits(args: dict[str, Any]) -> list[TextContent]:
    """List compliance audits with filters.

    Args:
        args: Tool arguments containing filter criteria

    Returns:
        JSON response with list of audits
    """
    status = args.get("status")
    audit_type = args.get("audit_type")
    start_date_str = args.get("start_date")
    end_date_str = args.get("end_date")
    limit = args.get("limit", 20)

    # Build query
    query = select(ComplianceAudit)

    # Apply filters
    if status:
        query = query.where(ComplianceAudit.status == status)
    if audit_type:
        query = query.where(ComplianceAudit.audit_type == audit_type)
    if start_date_str:
        start_date = date.fromisoformat(start_date_str)
        query = query.where(ComplianceAudit.start_date >= start_date)
    if end_date_str:
        end_date = date.fromisoformat(end_date_str)
        query = query.where(ComplianceAudit.end_date <= end_date)

    # Order and limit
    query = query.order_by(ComplianceAudit.start_date.desc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        audits = result.scalars().all()

    response = {
        "total_count": len(audits),
        "filters_applied": {
            "status": status,
            "audit_type": audit_type,
            "start_date": start_date_str,
            "end_date": end_date_str,
        },
        "audits": [
            {
                "audit_id": str(a.uuid),
                "audit_number": a.audit_number,
                "audit_name": a.audit_name,
                "audit_type": a.audit_type,
                "scope": a.scope,
                "status": a.status,
                "priority": a.priority,
                "start_date": a.start_date.isoformat(),
                "end_date": a.end_date.isoformat(),
                "days_remaining": (a.end_date - date.today()).days,
            }
            for a in audits
        ],
    }

    return json_response(response)
```

### Handler Best Practices

1. **Validation**: Always validate inputs before database operations
2. **Error Handling**: Use `error_response()` for user-facing errors
3. **Async**: All handlers must be `async` functions
4. **Session Management**: Use `async with async_session_factory()` pattern
5. **Return Type**: Always return `list[TextContent]`
6. **JSON Response**: Use `json_response()` helper for structured data
7. **UUID Handling**: Use `validate_uuid()` helper from base module

### Verification
```python
# Test handler directly (mock database)
python3 -c "
import asyncio
from corrdata.mcp.tools.compliance import handle_list_audits

async def test():
    result = await handle_list_audits({'status': 'in_progress', 'limit': 5})
    print(result[0].text)

asyncio.run(test())
"
```

## Step 4: Register Tool with Module Registry

### What You'll Do
Register your tool definitions with their handlers in the module's registry. This makes them available when the module is loaded.

### Files to Modify
- Same file (`src/corrdata/mcp/tools/compliance.py`)

### Code

```python
# Add at end of src/corrdata/mcp/tools/compliance.py

# =============================================================================
# Register all tools with their handlers
# =============================================================================

# ... existing registrations ...

# Register new audit tools
registry.register(create_audit_tool, handle_create_audit)
registry.register(get_audit_status_tool, handle_get_audit_status)
registry.register(list_audits_tool, handle_list_audits)
```

### Verification
```python
# Verify tools are registered
python3 -c "
from corrdata.mcp.tools.compliance import registry

tools = registry.list_tools()
tool_names = [t.name for t in tools]
print(f'Total tools: {len(tools)}')
print('Audit tools:', [n for n in tool_names if 'audit' in n])
"
```

## Step 5: Update server_v2.py Module Registration

### What You'll Do
Ensure your module is registered in the MCP server's module list. If you added to an existing module, no changes needed. If you created a new module, add it to `AVAILABLE_MODULES`.

### Files to Modify
- `src/corrdata/mcp/server_v2.py`

### Code

If creating a new module (e.g., `audit.py`):

```python
# In src/corrdata/mcp/server_v2.py

# Update AVAILABLE_MODULES dict
AVAILABLE_MODULES = {
    "core": "corrdata.mcp.tools.core",
    "predictive": "corrdata.mcp.tools.predictive",
    "external": "corrdata.mcp.tools.external",
    "alerts": "corrdata.mcp.tools.alerts",
    "survey": "corrdata.mcp.tools.survey",
    "gis": "corrdata.mcp.tools.gis",
    "phmsa": "corrdata.mcp.tools.phmsa",
    "mobile": "corrdata.mcp.tools.mobile",
    "compliance": "corrdata.mcp.tools.compliance",
    "audit": "corrdata.mcp.tools.audit",  # ADD THIS LINE
    # ... other modules ...
}
```

Update module documentation in docstring:

```python
"""
Available modules:
    ...
    compliance   - Regulatory compliance (6 tools)
    audit        - Compliance audit workflow (8 tools)  # ADD THIS
    ...
"""
```

### Verification
```bash
# Start MCP server with your module
CORRDATA_MCP_MODULES=compliance python -m corrdata.mcp

# In another terminal, check logs for module loading
# Should see: "mcp_module_loaded" with your module name
```

## Step 6: Write Comprehensive Tests

### What You'll Do
Create test file for your new tools, covering success cases, error cases, and edge cases.

### Files to Create
- `tests/test_mcp_audit_tools.py` (example)

### Code

```python
# tests/test_mcp_audit_tools.py

import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from corrdata.mcp.tools.compliance import (
    handle_create_audit,
    handle_get_audit_status,
    handle_list_audits,
)


class TestCreateAuditTool:
    """Test suite for create_compliance_audit tool."""

    @pytest.mark.asyncio
    async def test_create_audit_success(self):
        """Test successful audit creation."""
        args = {
            "audit_type": "internal",
            "audit_name": "Q4 2025 IMP Review",
            "scope": "integrity_management",
            "start_date": "2025-10-01",
            "end_date": "2025-10-15",
            "auditor_ids": ["auditor-001", "auditor-002"],
            "lead_auditor_id": "auditor-001",
            "regulation_ids": ["192.903", "192.911"],
            "priority": "high",
        }

        with patch("corrdata.mcp.tools.compliance.async_session_factory") as mock_factory:
            # Mock database session
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            # Mock regulation lookup
            mock_session.execute.return_value.scalars.return_value.all.return_value = [
                Mock(regulation_id="192.903"),
                Mock(regulation_id="192.911"),
            ]

            result = await handle_create_audit(args)

        # Parse JSON response
        response = json.loads(result[0].text)

        assert "audit_id" in response
        assert response["audit_number"].startswith("AUDIT-")
        assert response["audit_type"] == "internal"
        assert response["audit_name"] == "Q4 2025 IMP Review"
        assert response["status"] == "planned"
        assert response["auditor_count"] == 2
        assert response["regulation_count"] == 2

    @pytest.mark.asyncio
    async def test_create_audit_missing_required_field(self):
        """Test error when required field is missing."""
        args = {
            "audit_type": "internal",
            # Missing audit_name and scope
            "start_date": "2025-10-01",
            "end_date": "2025-10-15",
        }

        result = await handle_create_audit(args)
        response_text = result[0].text

        assert "required" in response_text.lower()

    @pytest.mark.asyncio
    async def test_create_audit_invalid_date_range(self):
        """Test error when end_date is before start_date."""
        args = {
            "audit_type": "internal",
            "audit_name": "Test Audit",
            "scope": "integrity_management",
            "start_date": "2025-10-15",
            "end_date": "2025-10-01",  # Before start
        }

        result = await handle_create_audit(args)
        response_text = result[0].text

        assert "end_date must be after start_date" in response_text

    @pytest.mark.asyncio
    async def test_create_audit_unknown_regulation(self):
        """Test error when regulation ID doesn't exist."""
        args = {
            "audit_type": "internal",
            "audit_name": "Test Audit",
            "scope": "integrity_management",
            "start_date": "2025-10-01",
            "end_date": "2025-10-15",
            "regulation_ids": ["INVALID-REG"],
        }

        with patch("corrdata.mcp.tools.compliance.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            # Mock empty regulation lookup
            mock_session.execute.return_value.scalars.return_value.all.return_value = []

            result = await handle_create_audit(args)

        response_text = result[0].text
        assert "Unknown regulation IDs" in response_text


class TestGetAuditStatusTool:
    """Test suite for get_audit_status tool."""

    @pytest.mark.asyncio
    async def test_get_audit_status_success(self):
        """Test successful audit status retrieval."""
        audit_uuid = uuid4()
        mock_audit = Mock(
            uuid=audit_uuid,
            audit_number="AUDIT-20251214-ABC123",
            audit_type="internal",
            audit_name="Test Audit",
            scope="integrity_management",
            status="in_progress",
            priority="high",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            lead_auditor_id="auditor-001",
            auditor_ids=["auditor-001", "auditor-002"],
            regulation_ids=["192.903"],
            description="Test audit description",
            completion_percentage=35,
            findings=[],
        )

        args = {"audit_id": str(audit_uuid), "include_findings": False}

        with patch("corrdata.mcp.tools.compliance.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_audit

            result = await handle_get_audit_status(args)

        response = json.loads(result[0].text)

        assert response["audit_id"] == str(audit_uuid)
        assert response["audit_number"] == "AUDIT-20251214-ABC123"
        assert response["status"] == "in_progress"
        assert response["progress"]["completion_percentage"] == 35
        assert "findings" not in response  # Not included when include_findings=False

    @pytest.mark.asyncio
    async def test_get_audit_status_not_found(self):
        """Test error when audit doesn't exist."""
        args = {"audit_id": str(uuid4())}

        with patch("corrdata.mcp.tools.compliance.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            result = await handle_get_audit_status(args)

        response_text = result[0].text
        assert "not found" in response_text.lower()


class TestListAuditsTool:
    """Test suite for list_compliance_audits tool."""

    @pytest.mark.asyncio
    async def test_list_audits_with_filters(self):
        """Test listing audits with status filter."""
        mock_audits = [
            Mock(
                uuid=uuid4(),
                audit_number="AUDIT-001",
                audit_name="Audit 1",
                audit_type="internal",
                scope="integrity_management",
                status="in_progress",
                priority="high",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=14),
            ),
            Mock(
                uuid=uuid4(),
                audit_number="AUDIT-002",
                audit_name="Audit 2",
                audit_type="phmsa",
                scope="full_compliance",
                status="in_progress",
                priority="critical",
                start_date=date.today() - timedelta(days=7),
                end_date=date.today() + timedelta(days=7),
            ),
        ]

        args = {"status": "in_progress", "limit": 10}

        with patch("corrdata.mcp.tools.compliance.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value.scalars.return_value.all.return_value = mock_audits

            result = await handle_list_audits(args)

        response = json.loads(result[0].text)

        assert response["total_count"] == 2
        assert response["filters_applied"]["status"] == "in_progress"
        assert len(response["audits"]) == 2
        assert all(a["status"] == "in_progress" for a in response["audits"])
```

### Verification
```bash
# Run tests
pytest tests/test_mcp_audit_tools.py -v

# Run with coverage
pytest tests/test_mcp_audit_tools.py --cov=corrdata.mcp.tools.compliance --cov-report=term-missing
```

## Step 7: Verify Tool Appears in list_tools()

### What You'll Do
Start the MCP server and verify your tool appears in the tool list and can be called.

### Verification Steps

**1. Check tool registration:**
```python
python3 -c "
from corrdata.mcp.tools.compliance import registry

tools = registry.list_tools()
for tool in tools:
    if 'audit' in tool.name:
        print(f'{tool.name}: {tool.description[:60]}...')
"
```

**2. Start MCP server with module:**
```bash
# Load compliance module
CORRDATA_MCP_MODULES=compliance python -m corrdata.mcp
```

**3. Test tool call (if using Claude Desktop or MCP client):**
```json
{
  "method": "tools/call",
  "params": {
    "name": "create_compliance_audit",
    "arguments": {
      "audit_type": "internal",
      "audit_name": "Test Audit",
      "scope": "integrity_management",
      "start_date": "2025-11-01",
      "end_date": "2025-11-15"
    }
  }
}
```

Expected: Tool executes and returns JSON response with audit details.

## Step 8: Document Usage and Examples

### What You'll Do
Create documentation showing how to use your tool, including example workflows and common use cases.

### Files to Create/Modify
- `docs/examples/mcp-audit-workflow.md` (example)

### Code

```markdown
# MCP Tool: Compliance Audit Workflow

## Overview
The compliance audit tools enable LLMs to manage the full audit lifecycle:
create audits, track progress, record findings, and generate reports.

## Tools Available
- `create_compliance_audit` - Create new audit
- `get_audit_status` - Check audit progress
- `list_compliance_audits` - List/filter audits

## Example Workflows

### Create Internal Audit
```
User: "Create an internal audit for integrity management starting next month"

LLM calls:
{
  "tool": "create_compliance_audit",
  "args": {
    "audit_type": "internal",
    "audit_name": "Q1 2026 IMP Internal Audit",
    "scope": "integrity_management",
    "start_date": "2026-01-02",
    "end_date": "2026-01-16",
    "priority": "high"
  }
}

Response:
{
  "audit_id": "550e8400-e29b-41d4-a716-446655440000",
  "audit_number": "AUDIT-20251214-A1B2C3",
  "status": "planned",
  "message": "Audit AUDIT-20251214-A1B2C3 created successfully"
}
```

### Check Audit Progress
```
User: "What's the status of audit AUDIT-20251214-A1B2C3?"

LLM calls:
{
  "tool": "get_audit_status",
  "args": {
    "audit_id": "AUDIT-20251214-A1B2C3",
    "include_findings": true
  }
}

Response shows:
- Current status (planned/in_progress/review/completed)
- Days remaining
- Completion percentage
- Findings summary
```

### List Active Audits
```
User: "Show me all in-progress PHMSA audits"

LLM calls:
{
  "tool": "list_compliance_audits",
  "args": {
    "status": "in_progress",
    "audit_type": "phmsa",
    "limit": 20
  }
}
```

## Integration with Other Tools

Audit tools work seamlessly with other compliance tools:

1. **Check compliance before audit**:
   - `get_compliance_status` → `create_compliance_audit`

2. **Validate data completeness**:
   - `validate_data_completeness` → Include results in audit

3. **Generate reports after audit**:
   - `get_audit_status` → `generate_annual_report`
```

### Verification
- Documentation is clear and complete
- Examples are tested and work
- Workflow patterns are documented

## Troubleshooting

### Common Issue 1: Tool Not Appearing in list_tools()
**Symptom**: Tool doesn't show up when calling `list_tools()`

**Solution**: Verify registration chain:
```python
# 1. Check module registry
from corrdata.mcp.tools.compliance import registry
print([t.name for t in registry.list_tools()])

# 2. Check module is loaded in server
# In server_v2.py logs, look for "mcp_module_loaded"

# 3. Verify CORRDATA_MCP_MODULES includes your module
echo $CORRDATA_MCP_MODULES
```

### Common Issue 2: Handler Errors Not Showing
**Symptom**: Tool fails silently or returns generic error

**Solution**: Check handler wraps errors properly:
```python
# Always return error_response() for user errors
if not required_field:
    return error_response("field_name is required")

# Let system errors propagate (they're caught by registry)
# Don't catch unexpected exceptions in handlers
```

### Common Issue 3: Import Errors
**Symptom**: `ImportError` or `ModuleNotFoundError` when loading module

**Solution**: Check imports and module structure:
```python
# In tool module file, verify imports
from corrdata.mcp.tools import Param, ToolDefinition, ToolRegistry  # Base imports
from corrdata.mcp.tools.base import error_response, json_response  # Helpers
from corrdata.db.session import async_session_factory  # Database

# Ensure module has registry export
registry = ToolRegistry()  # Must be module-level
```

### Common Issue 4: Async/Await Issues
**Symptom**: `RuntimeWarning: coroutine was never awaited`

**Solution**: Ensure all async operations are awaited:
```python
# WRONG - missing await
result = session.execute(query)

# CORRECT
result = await session.execute(query)

# WRONG - async handler without async
def handle_my_tool(args):
    return await some_async_call()

# CORRECT
async def handle_my_tool(args):
    return await some_async_call()
```

## Learnings

### From Sprint 80 (Modular MCP Architecture)
- Keep modules focused on specific domains
- Use lazy loading to reduce context usage
- Document tool count and context percentage
- Provide granular module loading options

### From Sprint 103 (Compliance GraphQL Module)
- Standardize on common patterns (audit workflow, finding tracking)
- Reuse parameter definitions across similar tools
- Provide both UUID and human-readable ID lookups
- Include progress tracking in status tools

### From Sprint 34 (Calendar Tools)
- Date handling should be flexible (ISO 8601 strings)
- Always validate date ranges (start < end)
- Provide clear error messages for date parse failures
- Return dates in consistent ISO format

## Related

- [Pattern: MCP Tool Registry](../patterns/mcp-tool-registry.md)
- [Playbook: Adding External Data Source](./adding-external-data-source.md)
- [ADR-024: Modular MCP Architecture](../../architecture/decisions/ADR-024-modular-mcp-architecture.md)
- [ADR-034: MCP Tool Registry](../../architecture/decisions/ADR-034-mcp-tool-registry.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version - comprehensive MCP tool onboarding guide |
