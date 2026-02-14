# Playbook: Creating a New REST Endpoint

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2025-12-14
**Estimated Time**: 1-2 hours
**Prerequisites**:
- Python 3.11+
- Understanding of FastAPI and Pydantic
- Knowledge of async Python
- Familiarity with SQLAlchemy 2.0
- Understanding of REST API design principles

**Related Patterns**:
- [FastAPI Hybrid API (ADR-019)](../../architecture/decisions/ADR-019-fastapi-hybrid-api.md)
- [GraphQL API (ADR-002)](../../architecture/decisions/ADR-002-graphql-api.md)
- [Mixin Model Composition (ADR-035)](../../architecture/decisions/ADR-035-mixin-model-composition.md)

## Overview

This playbook guides you through creating a new REST endpoint in CorrData's FastAPI application. While GraphQL is preferred for most data operations, REST endpoints are appropriate for:
- File uploads/downloads
- Webhooks and callbacks
- Mobile app offline sync
- Legacy system integrations
- Operations that don't fit GraphQL patterns

CorrData uses a hybrid API approach: GraphQL for queries and mutations, REST for special-purpose operations.

## When to Use This Playbook

- You need to handle file uploads or binary data
- You're implementing a webhook endpoint for external services
- You need streaming responses or server-sent events
- You're building batch sync for offline mobile operations
- You have a specific HTTP method requirement (PATCH, HEAD, etc.)
- The operation doesn't map well to GraphQL query/mutation pattern

## When NOT to Use REST (Use GraphQL Instead)

- Standard CRUD operations on entities
- Querying related data (leverages GraphQL's relationship graph)
- Filtering, sorting, pagination of data
- Real-time subscriptions
- Type-safe frontend integration with code generation

## Checklist

- [ ] Step 1: Determine if REST is needed (vs GraphQL)
- [ ] Step 2: Create Pydantic request/response models
- [ ] Step 3: Create router module for endpoint group
- [ ] Step 4: Implement route handler with validation
- [ ] Step 5: Add authentication/authorization
- [ ] Step 6: Register router in FastAPI app
- [ ] Step 7: Write comprehensive tests
- [ ] Step 8: Document in OpenAPI/Swagger

## Step 1: Determine If REST Is Needed

### What You'll Do
Evaluate whether your use case is better served by REST or GraphQL. This decision affects maintainability and frontend integration.

### Decision Matrix

| Use Case | REST | GraphQL | Reason |
|----------|------|---------|--------|
| File upload | Yes | No | Binary data, multipart/form-data |
| File download | Yes | No | Streaming responses |
| Webhook receiver | Yes | No | External system calls us |
| Batch sync | Yes | No | Complex offline reconciliation |
| Get entity by ID | No | Yes | Standard query, type-safe |
| List/filter entities | No | Yes | Better filtering, pagination |
| Update entity fields | No | Yes | Partial updates, type-safe |
| Complex queries | No | Yes | Relationship traversal |

### Example Decision

**Scenario**: Need to export compliance audit findings as PDF

**Analysis**:
- Operation: Generate and download PDF file
- Response type: Binary (application/pdf)
- Caching: Can use HTTP caching headers
- GraphQL fit: Poor (binary data, streaming)

**Decision**: Use REST endpoint
- Endpoint: `GET /api/v1/compliance/audits/{audit_id}/export-pdf`
- Returns: StreamingResponse with PDF

**Alternative Scenario**: Need to list all audits with filters

**Analysis**:
- Operation: Query with filters (status, date range, type)
- Response type: JSON array of objects
- Related data: Want to include assigned auditors, regulations
- Frontend: React with GraphQL code generation

**Decision**: Use GraphQL
- Query: `audits(status: "in_progress", limit: 20) { ... }`
- Benefits: Type safety, relationship loading, code generation

### Verification
- Decision documented with rationale
- Alternative approaches considered
- Team agrees on approach

## Step 2: Create Pydantic Request/Response Models

### What You'll Do
Define strongly-typed request and response models using Pydantic. Use base mixins for common fields (UUIDs, timestamps).

### Files to Create/Modify
- New router module (e.g., `src/corrdata/api/export_routes.py`)

### Code

Let's create an endpoint for exporting audit findings as various formats:

```python
# src/corrdata/api/export_routes.py

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corrdata.api.models_base import TimestampMixin, UUIDMixin
from corrdata.db.models import ComplianceAudit
from corrdata.db.session import async_session_factory

router = APIRouter(prefix="/api/v1/export", tags=["Export"])


# =============================================================================
# Enums
# =============================================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ExportStatus(str, Enum):
    """Status of export job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Request Models
# =============================================================================

class AuditExportRequest(BaseModel):
    """Request model for audit export."""

    model_config = ConfigDict(use_enum_values=True)

    audit_id: UUID = Field(..., description="UUID of the audit to export")
    format: ExportFormat = Field(
        default=ExportFormat.PDF,
        description="Export format (pdf, csv, xlsx, json)"
    )
    include_attachments: bool = Field(
        default=False,
        description="Include finding attachments in export"
    )
    include_photos: bool = Field(
        default=False,
        description="Include photos in export"
    )
    sections: list[str] | None = Field(
        default=None,
        description="Specific sections to include (null = all sections)"
    )

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, v):
        """Validate section names."""
        if v is None:
            return v

        valid_sections = {
            "summary",
            "findings",
            "recommendations",
            "timeline",
            "attachments",
            "regulations",
        }
        invalid = set(v) - valid_sections
        if invalid:
            raise ValueError(f"Invalid sections: {', '.join(invalid)}")
        return v


class BatchExportRequest(BaseModel):
    """Request model for batch export."""

    entity_type: str = Field(..., description="Type of entities to export")
    entity_ids: list[UUID] = Field(..., description="List of entity UUIDs to export")
    format: ExportFormat = Field(default=ExportFormat.CSV)
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Additional filters to apply"
    )

    @field_validator("entity_ids")
    @classmethod
    def validate_entity_ids(cls, v):
        """Validate entity ID list."""
        if not v:
            raise ValueError("entity_ids cannot be empty")
        if len(v) > 1000:
            raise ValueError("Cannot export more than 1000 entities at once")
        return v


# =============================================================================
# Response Models
# =============================================================================

class ExportJobResponse(UUIDMixin, TimestampMixin):
    """Response model for export job. Uses UUID and timestamp mixins."""

    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: ExportStatus
    format: ExportFormat
    entity_type: str
    entity_count: int
    download_url: str | None = None
    error_message: str | None = None
    expires_at: datetime | None = None


class ExportMetadata(BaseModel):
    """Metadata included in export files."""

    export_date: datetime
    exported_by: str
    entity_type: str
    entity_count: int
    format: str
    filters_applied: dict[str, Any] | None = None
    corrdata_version: str = "0.1.0"


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_factory() as session:
        yield session


async def get_current_user():
    """Get current authenticated user.

    TODO: Implement proper authentication.
    For now, returns mock user.
    """
    return {"user_id": "user-001", "username": "demo_user"}
```

### Model Best Practices

1. **Use Mixins**: Inherit from `UUIDMixin` and `TimestampMixin` for common fields
2. **Field Descriptions**: Always provide `Field(..., description="...")` for OpenAPI docs
3. **Validators**: Use `@field_validator` for complex validation logic
4. **Enums**: Use `str, Enum` for fixed choice fields
5. **ConfigDict**: Set `from_attributes=True` for ORM model conversion
6. **Type Hints**: Always use proper type hints (str, int, UUID, datetime, etc.)

### Verification
```python
# Test models
python3 -c "
from corrdata.api.export_routes import AuditExportRequest, ExportFormat
from uuid import uuid4

# Valid request
req = AuditExportRequest(
    audit_id=uuid4(),
    format=ExportFormat.PDF,
    sections=['summary', 'findings']
)
print('Valid:', req.model_dump())

# Invalid sections (should raise)
try:
    bad = AuditExportRequest(audit_id=uuid4(), sections=['invalid'])
except ValueError as e:
    print('Caught expected error:', e)
"
```

## Step 3: Create Router Module for Endpoint Group

### What You'll Do
Create a FastAPI router to group related endpoints. Routers provide modular organization and can have shared prefix, tags, and dependencies.

### Files Already Modified
- `src/corrdata/api/export_routes.py` (started in Step 2)

### Code

Continue in `export_routes.py`:

```python
# src/corrdata/api/export_routes.py (continued)

import io
import json
from uuid import uuid4

# =============================================================================
# Helper Functions
# =============================================================================

def generate_pdf_export(audit_data: dict, options: dict) -> bytes:
    """Generate PDF export from audit data.

    Args:
        audit_data: Audit data dictionary
        options: Export options (include_attachments, etc.)

    Returns:
        PDF file as bytes
    """
    # TODO: Implement actual PDF generation
    # For now, return mock PDF
    pdf_content = f"""
    Mock PDF Export
    ===============

    Audit: {audit_data['audit_name']}
    Status: {audit_data['status']}

    Findings: {len(audit_data.get('findings', []))}

    Generated: {datetime.now().isoformat()}
    """.encode('utf-8')

    return pdf_content


def generate_csv_export(data: list[dict]) -> str:
    """Generate CSV export from data.

    Args:
        data: List of dictionaries to export

    Returns:
        CSV content as string
    """
    import csv
    import io

    if not data:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def generate_xlsx_export(data: list[dict]) -> bytes:
    """Generate Excel export from data.

    Args:
        data: List of dictionaries to export

    Returns:
        Excel file as bytes
    """
    # TODO: Implement with openpyxl or xlsxwriter
    # For now, return CSV as mock
    return generate_csv_export(data).encode('utf-8')
```

### Verification
```python
# Test helper functions
python3 -c "
from corrdata.api.export_routes import generate_csv_export

data = [
    {'id': 1, 'name': 'Test 1', 'status': 'active'},
    {'id': 2, 'name': 'Test 2', 'status': 'inactive'},
]

csv = generate_csv_export(data)
print('CSV output:')
print(csv)
"
```

## Step 4: Implement Route Handler with Validation

### What You'll Do
Implement the actual endpoint handlers with proper error handling, validation, and response formatting.

### Files to Modify
- `src/corrdata/api/export_routes.py` (continue)

### Code

```python
# src/corrdata/api/export_routes.py (continued)

# =============================================================================
# Route Handlers
# =============================================================================

@router.get("/audits/{audit_id}/export")
async def export_audit(
    audit_id: UUID,
    format: ExportFormat = Query(
        default=ExportFormat.PDF,
        description="Export format"
    ),
    include_attachments: bool = Query(
        default=False,
        description="Include attachments"
    ),
    include_photos: bool = Query(
        default=False,
        description="Include photos"
    ),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """Export a compliance audit in specified format.

    Returns the exported file as a download.

    - **audit_id**: UUID of the audit to export
    - **format**: Export format (pdf, csv, xlsx, json)
    - **include_attachments**: Include finding attachments
    - **include_photos**: Include photos

    Returns:
        StreamingResponse with exported file
    """
    # Fetch audit from database
    result = await session.execute(
        select(ComplianceAudit).where(ComplianceAudit.uuid == audit_id)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit not found: {audit_id}")

    # Prepare audit data for export
    audit_data = {
        "audit_id": str(audit.uuid),
        "audit_number": audit.audit_number,
        "audit_name": audit.audit_name,
        "audit_type": audit.audit_type,
        "scope": audit.scope,
        "status": audit.status,
        "start_date": audit.start_date.isoformat(),
        "end_date": audit.end_date.isoformat(),
        "findings": [],  # TODO: Load findings
    }

    # Generate export based on format
    if format == ExportFormat.PDF:
        content = generate_pdf_export(audit_data, {
            "include_attachments": include_attachments,
            "include_photos": include_photos,
        })
        media_type = "application/pdf"
        filename = f"{audit.audit_number}_export.pdf"

    elif format == ExportFormat.CSV:
        # For CSV, flatten audit data
        csv_data = [{
            "Audit Number": audit.audit_number,
            "Name": audit.audit_name,
            "Type": audit.audit_type,
            "Status": audit.status,
            "Start Date": audit.start_date.isoformat(),
            "End Date": audit.end_date.isoformat(),
        }]
        content = generate_csv_export(csv_data).encode('utf-8')
        media_type = "text/csv"
        filename = f"{audit.audit_number}_export.csv"

    elif format == ExportFormat.XLSX:
        xlsx_data = [{
            "Audit Number": audit.audit_number,
            "Name": audit.audit_name,
            "Type": audit.audit_type,
            "Status": audit.status,
            "Start Date": audit.start_date.isoformat(),
            "End Date": audit.end_date.isoformat(),
        }]
        content = generate_xlsx_export(xlsx_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{audit.audit_number}_export.xlsx"

    else:  # JSON
        content = json.dumps(audit_data, indent=2, default=str).encode('utf-8')
        media_type = "application/json"
        filename = f"{audit.audit_number}_export.json"

    # Return as streaming response with download headers
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Date": datetime.now().isoformat(),
            "X-Exported-By": current_user["username"],
        }
    )


@router.post("/batch", response_model=ExportJobResponse)
async def create_batch_export(
    request: BatchExportRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """Create a batch export job.

    For large exports, creates an async job and returns job ID.
    Client polls job status endpoint to check completion.

    - **entity_type**: Type of entities to export
    - **entity_ids**: List of entity UUIDs
    - **format**: Export format
    - **filters**: Additional filters

    Returns:
        Export job information with job_id
    """
    # Validate entity type
    valid_types = ["audit", "finding", "regulation", "submission"]
    if request.entity_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type. Must be one of: {', '.join(valid_types)}"
        )

    # Create export job
    job_id = f"EXPORT-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

    # TODO: Queue actual export job for background processing
    # For now, return mock job response

    response = ExportJobResponse(
        uuid=uuid4(),
        job_id=job_id,
        status=ExportStatus.PENDING,
        format=request.format,
        entity_type=request.entity_type,
        entity_count=len(request.entity_ids),
        created_at=datetime.now(),
    )

    return response


@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """Get status of an export job.

    - **job_id**: Export job ID

    Returns:
        Export job status and download URL if completed
    """
    # TODO: Implement actual job lookup
    # For now, return mock completed job

    response = ExportJobResponse(
        uuid=uuid4(),
        job_id=job_id,
        status=ExportStatus.COMPLETED,
        format=ExportFormat.CSV,
        entity_type="audit",
        entity_count=10,
        download_url=f"/api/v1/export/download/{job_id}",
        created_at=datetime.now(),
    )

    return response
```

### Handler Best Practices

1. **Async All The Way**: Use `async def` and `await` for all database operations
2. **Dependency Injection**: Use `Depends()` for session, auth, etc.
3. **Error Handling**: Raise `HTTPException` with appropriate status codes
4. **Type Hints**: Include return type hints for better OpenAPI docs
5. **Docstrings**: Write detailed docstrings (shown in Swagger UI)
6. **Query Parameters**: Use `Query()` for validation and documentation
7. **Path Parameters**: Validate path params (UUID, etc.)

### Verification
```bash
# Start the API server
PYTHONPATH=src uvicorn corrdata.api.app:app --reload

# Test endpoint (in another terminal)
curl -X GET "http://localhost:8000/api/v1/export/audits/550e8400-e29b-41d4-a716-446655440000/export?format=json"
```

## Step 5: Add Authentication/Authorization

### What You'll Do
Implement proper authentication and authorization for your endpoint. CorrData uses JWT tokens for API authentication.

### Files to Modify
- `src/corrdata/api/export_routes.py` (update dependencies)

### Code

```python
# Update dependency in src/corrdata/api/export_routes.py

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

# =============================================================================
# Authentication Dependencies
# =============================================================================

SECRET_KEY = "your-secret-key-here"  # TODO: Move to environment config
ALGORITHM = "HS256"


async def verify_token(authorization: str = Header(None)):
    """Verify JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_payload: dict = Depends(verify_token)):
    """Get current user from verified token.

    Args:
        token_payload: Decoded JWT payload

    Returns:
        User information dictionary

    Raises:
        HTTPException: If user not found
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # TODO: Load user from database
    # For now, return user info from token
    return {
        "user_id": user_id,
        "username": token_payload.get("username", "unknown"),
        "email": token_payload.get("email"),
        "roles": token_payload.get("roles", []),
    }


def require_role(required_role: str):
    """Dependency factory for role-based access control.

    Args:
        required_role: Role required to access endpoint

    Returns:
        Dependency function that checks user role
    """
    async def check_role(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if required_role not in user_roles and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}"
            )
        return current_user

    return check_role


# =============================================================================
# Update route handlers to use authentication
# =============================================================================

@router.get("/audits/{audit_id}/export")
async def export_audit(
    audit_id: UUID,
    format: ExportFormat = Query(default=ExportFormat.PDF),
    include_attachments: bool = Query(default=False),
    include_photos: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),  # Requires auth
):
    """Export a compliance audit (authentication required)."""
    # ... implementation from Step 4 ...
    pass


@router.post("/batch", response_model=ExportJobResponse)
async def create_batch_export(
    request: BatchExportRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_role("auditor")),  # Requires 'auditor' role
):
    """Create batch export (requires auditor role)."""
    # ... implementation from Step 4 ...
    pass
```

### Authorization Patterns

**1. Require Authentication Only:**
```python
current_user: dict = Depends(get_current_user)
```

**2. Require Specific Role:**
```python
current_user: dict = Depends(require_role("auditor"))
```

**3. Require Multiple Roles (OR):**
```python
def require_any_role(*roles: str):
    async def check_roles(user: dict = Depends(get_current_user)):
        if not any(r in user.get("roles", []) for r in roles):
            raise HTTPException(403, f"Requires one of: {', '.join(roles)}")
        return user
    return check_roles

# Usage
current_user: dict = Depends(require_any_role("auditor", "admin"))
```

**4. Resource-Level Authorization:**
```python
async def verify_audit_access(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Verify user has access to specific audit."""
    # Check if user owns audit or has admin role
    # Raise 403 if not authorized
    pass
```

### Verification
```bash
# Test without auth (should fail)
curl -X GET "http://localhost:8000/api/v1/export/audits/550e8400-e29b-41d4-a716-446655440000/export"
# Expected: 401 Unauthorized

# Test with invalid token (should fail)
curl -X GET "http://localhost:8000/api/v1/export/audits/550e8400-e29b-41d4-a716-446655440000/export" \
  -H "Authorization: Bearer invalid-token"
# Expected: 401 Unauthorized

# Test with valid token (should succeed)
# First, generate a token (for testing)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
# Use returned token in subsequent requests
```

## Step 6: Register Router in FastAPI App

### What You'll Do
Register your new router with the main FastAPI application so endpoints are accessible.

### Files to Modify
- `src/corrdata/api/app.py`

### Code

```python
# In src/corrdata/api/app.py

from corrdata.api.export_routes import router as export_router  # ADD THIS IMPORT

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CorrData API",
        description="Digital Twin Platform for Pipeline Integrity Intelligence",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ... existing middleware ...

    # GraphQL router
    graphql_router = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_router, prefix="/graphql")

    # REST API routers
    app.include_router(geo_router)
    app.include_router(mobile_router)
    app.include_router(auth_router)
    app.include_router(upload_router)
    app.include_router(document_router)
    app.include_router(export_router)  # ADD THIS LINE

    # ... rest of app setup ...

    return app
```

### Verification
```bash
# Restart API server
PYTHONPATH=src uvicorn corrdata.api.app:app --reload

# Check OpenAPI schema includes new endpoints
curl http://localhost:8000/openapi.json | jq '.paths | keys' | grep export

# Visit Swagger UI
open http://localhost:8000/docs
# Should see "Export" section with your endpoints
```

## Step 7: Write Comprehensive Tests

### What You'll Do
Create comprehensive test suite covering success cases, error cases, authentication, and edge cases.

### Files to Create
- `tests/test_export_routes.py`

### Code

```python
# tests/test_export_routes.py

from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from corrdata.api.app import create_app
from corrdata.api.export_routes import SECRET_KEY, ALGORITHM


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create valid auth token for testing."""
    payload = {
        "sub": "user-001",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["auditor"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


@pytest.fixture
def admin_token():
    """Create admin auth token."""
    payload = {
        "sub": "admin-001",
        "username": "admin",
        "roles": ["admin"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


class TestExportAuditEndpoint:
    """Test suite for audit export endpoint."""

    def test_export_audit_pdf_success(self, client, auth_token):
        """Test successful PDF export."""
        audit_id = uuid4()

        with patch("corrdata.api.export_routes.async_session_factory") as mock_factory:
            # Mock database session and audit
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_audit = Mock(
                uuid=audit_id,
                audit_number="AUDIT-001",
                audit_name="Test Audit",
                audit_type="internal",
                scope="integrity_management",
                status="completed",
                start_date=date.today() - timedelta(days=14),
                end_date=date.today(),
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_audit

            # Make request
            response = client.get(
                f"/api/v1/export/audits/{audit_id}/export?format=pdf",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "AUDIT-001" in response.headers["content-disposition"]

    def test_export_audit_csv_success(self, client, auth_token):
        """Test successful CSV export."""
        audit_id = uuid4()

        with patch("corrdata.api.export_routes.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_audit = Mock(
                uuid=audit_id,
                audit_number="AUDIT-002",
                audit_name="CSV Test",
                audit_type="phmsa",
                scope="full_compliance",
                status="in_progress",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_audit

            response = client.get(
                f"/api/v1/export/audits/{audit_id}/export?format=csv",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        # Verify CSV content
        csv_content = response.text
        assert "AUDIT-002" in csv_content
        assert "CSV Test" in csv_content

    def test_export_audit_not_found(self, client, auth_token):
        """Test export of non-existent audit."""
        audit_id = uuid4()

        with patch("corrdata.api.export_routes.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            response = client.get(
                f"/api/v1/export/audits/{audit_id}/export",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_audit_unauthorized(self, client):
        """Test export without authentication."""
        audit_id = uuid4()

        response = client.get(f"/api/v1/export/audits/{audit_id}/export")

        assert response.status_code == 401
        assert "authorization" in response.json()["detail"].lower()

    def test_export_audit_invalid_token(self, client):
        """Test export with invalid token."""
        audit_id = uuid4()

        response = client.get(
            f"/api/v1/export/audits/{audit_id}/export",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401


class TestBatchExportEndpoint:
    """Test suite for batch export endpoint."""

    def test_create_batch_export_success(self, client, auth_token):
        """Test successful batch export creation."""
        request_data = {
            "entity_type": "audit",
            "entity_ids": [str(uuid4()) for _ in range(5)],
            "format": "csv",
        }

        response = client.post(
            "/api/v1/export/batch",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["entity_count"] == 5
        assert data["format"] == "csv"

    def test_create_batch_export_invalid_type(self, client, auth_token):
        """Test batch export with invalid entity type."""
        request_data = {
            "entity_type": "invalid_type",
            "entity_ids": [str(uuid4())],
            "format": "csv",
        }

        response = client.post(
            "/api/v1/export/batch",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "Invalid entity_type" in response.json()["detail"]

    def test_create_batch_export_too_many_entities(self, client, auth_token):
        """Test batch export with too many entities."""
        request_data = {
            "entity_type": "audit",
            "entity_ids": [str(uuid4()) for _ in range(1001)],  # Over limit
            "format": "csv",
        }

        response = client.post(
            "/api/v1/export/batch",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 422  # Validation error
        assert "Cannot export more than 1000" in str(response.json())

    def test_create_batch_export_requires_auditor_role(self, client):
        """Test batch export requires auditor role."""
        # Create token without auditor role
        payload = {
            "sub": "user-002",
            "username": "viewer",
            "roles": ["viewer"],  # Not auditor
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        request_data = {
            "entity_type": "audit",
            "entity_ids": [str(uuid4())],
            "format": "csv",
        }

        response = client.post(
            "/api/v1/export/batch",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "role" in response.json()["detail"].lower()


class TestExportJobStatusEndpoint:
    """Test suite for export job status endpoint."""

    def test_get_job_status_success(self, client, auth_token):
        """Test getting export job status."""
        job_id = "EXPORT-20251214-ABC123"

        response = client.get(
            f"/api/v1/export/jobs/{job_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "download_url" in data
```

### Verification
```bash
# Run tests
pytest tests/test_export_routes.py -v

# Run with coverage
pytest tests/test_export_routes.py --cov=corrdata.api.export_routes --cov-report=term-missing

# Expected: All tests pass with >85% coverage
```

## Step 8: Document in OpenAPI/Swagger

### What You'll Do
Ensure your endpoints are well-documented in OpenAPI schema with examples, descriptions, and proper schemas.

### Files Already Modified
- Docstrings and Field descriptions provide automatic OpenAPI docs

### Verification Steps

**1. Check OpenAPI schema:**
```bash
# View full OpenAPI schema
curl http://localhost:8000/openapi.json | jq '.paths."/api/v1/export/audits/{audit_id}/export"'
```

**2. Visit Swagger UI:**
```bash
# Open in browser
open http://localhost:8000/docs
```

**3. Test in Swagger UI:**
- Navigate to "Export" section
- Click "Try it out" on `/export/audits/{audit_id}/export`
- Enter test UUID
- Select format
- Execute request

**4. Check ReDoc:**
```bash
# Alternative documentation view
open http://localhost:8000/redoc
```

### Enhancing Documentation

Add response examples:

```python
@router.get(
    "/audits/{audit_id}/export",
    responses={
        200: {
            "description": "Successful export",
            "content": {
                "application/pdf": {
                    "example": "Binary PDF content"
                },
                "application/json": {
                    "example": {
                        "audit_id": "550e8400-e29b-41d4-a716-446655440000",
                        "audit_name": "Q4 2025 IMP Review",
                        "status": "completed"
                    }
                }
            }
        },
        404: {
            "description": "Audit not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Audit not found: <uuid>"}
                }
            }
        }
    }
)
async def export_audit(...):
    """Export compliance audit."""
    pass
```

## Troubleshooting

### Common Issue 1: "405 Method Not Allowed"
**Symptom**: Endpoint returns 405 error

**Solution**: Check HTTP method matches decorator:
```python
# WRONG - GET decorator, POST request
@router.get("/endpoint")
async def my_endpoint(...):

# CORRECT
@router.post("/endpoint")
async def my_endpoint(...):
```

### Common Issue 2: Pydantic Validation Errors
**Symptom**: 422 Unprocessable Entity with validation errors

**Solution**: Check request body matches model schema:
```python
# Enable detailed error messages
from fastapi import FastAPI
app = FastAPI(debug=True)

# Check model accepts data
request_data = {...}
model = MyRequestModel(**request_data)  # Test in isolation
```

### Common Issue 3: Async Session Context Issues
**Symptom**: `RuntimeError: Session is closed`

**Solution**: Use async context manager:
```python
# WRONG - session not properly awaited
session = async_session_factory()
result = await session.execute(query)

# CORRECT
async with async_session_factory() as session:
    result = await session.execute(query)
```

### Common Issue 4: StreamingResponse Not Downloading
**Symptom**: Browser displays content instead of downloading

**Solution**: Add Content-Disposition header:
```python
return StreamingResponse(
    content,
    media_type="application/pdf",
    headers={
        "Content-Disposition": 'attachment; filename="export.pdf"'  # Key!
    }
)
```

## Learnings

### From Sprint 9 (Mobile Routes)
- Use Pydantic mixins for common fields (UUIDMixin, TimestampMixin)
- Implement proper pagination with limit/offset
- Include metadata in responses (total count, filters applied)
- Use Field() descriptions for better API docs

### From Sprint 19 (FastAPI Hybrid API)
- Prefer GraphQL for data queries
- Use REST for file operations and webhooks
- Keep routers modular and domain-focused
- Share authentication between GraphQL and REST

### From Sprint 44 (Testing Strategy)
- Test both success and error cases
- Mock database sessions for fast tests
- Test authentication and authorization separately
- Verify response schemas match Pydantic models

## Related

- [Playbook: Onboarding MCP Tool](./onboarding-mcp-tool.md)
- [Playbook: Adding External Data Source](./adding-external-data-source.md)
- [ADR-019: FastAPI Hybrid API](../../architecture/decisions/ADR-019-fastapi-hybrid-api.md)
- [ADR-002: GraphQL API](../../architecture/decisions/ADR-002-graphql-api.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version - comprehensive REST endpoint creation guide |
