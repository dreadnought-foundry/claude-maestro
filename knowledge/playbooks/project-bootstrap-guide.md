# Project Bootstrap Guide

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2026-01-02

---

## Context

### When to Use This Guide

- Starting a new full-stack project from scratch
- Team member needs to set up a new service/application
- Creating a proof-of-concept or MVP
- Spinning up a new microservice in your ecosystem

### When NOT to Use

- Adding features to existing projects (use sprint workflow)
- Quick prototypes that won't go to production
- Projects with radically different tech requirements (mobile-only, embedded systems, etc.)

---

## Overview

This guide walks you through creating a new project from the full-stack template in the correct order. By the end, you'll have:

- Working backend API with GraphQL
- Working frontend with type-safe queries
- Database with migrations
- Docker-based local development
- Ready for first feature sprint

**Time estimate:** 2-4 hours for first project, 30 minutes after you've done it once.

---

## Prerequisites

**Required:**
- [ ] Docker Desktop installed and running
- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] Git installed
- [ ] Code editor (VS Code recommended)
- [ ] Terminal access

**Recommended:**
- [ ] Claude Code CLI installed
- [ ] ai-playbook cloned locally
- [ ] PostgreSQL client (TablePlus, pgAdmin, or psql)

---

## Step-by-Step Bootstrap

### Phase 0: Planning (15 minutes)

Before touching code, answer these questions:

**1. What are you building?**
- One sentence description: _____________________________
- Who are the users? _____________________________
- What's the core value proposition? _____________________________

**2. What's your domain model?**

List 3-5 core entities (nouns in your system):
- Example: Task management app → Project, Task, User, Comment
- Your app: _________________, _________________, _________________

**3. Do you need these features now?**
- [ ] Multi-tenancy (multiple organizations)
- [ ] Spatial data (maps, locations)
- [ ] Time-series data (metrics over time)
- [ ] Real-time updates (WebSockets)
- [ ] File uploads
- [ ] Authentication (yes, you probably do)

Write this down - you'll reference it throughout bootstrap.

---

### Phase 1: Create Project from Template (30 minutes)

#### 1.1 Copy Template

```bash
# Navigate to where you want your project
cd ~/Development

# Copy template (or use init script)
cp -r ai-playbook/templates/full-stack-template ./my-project
cd my-project

# Or use the init script (recommended)
~/Development/ai-playbook/scripts/init-from-template.sh my-project "My Project Name"
```

#### 1.2 Initialize Environment

```bash
# Initialize project
make init

# This will:
# - Copy .env.example files
# - Install Python dependencies
# - Install Node dependencies
```

#### 1.3 Customize Project Metadata

Edit these files:

**backend/pyproject.toml:**
```toml
[project]
name = "my-project-backend"  # Change this
description = "Your description"  # Change this
```

**frontend/package.json:**
```json
{
  "name": "my-project-frontend",  // Change this
  "description": "Your description"  // Change this
}
```

**docker-compose.yml:**
```yaml
services:
  postgres:
    container_name: my-project-postgres  # Change this
  backend:
    container_name: my-project-backend   # Change this
  frontend:
    container_name: my-project-frontend  # Change this
```

#### 1.4 Start Services

```bash
# Start database
make db

# Wait for healthy status
docker-compose ps
```

#### 1.5 Verify Setup

```bash
# In one terminal: Start backend
make backend

# In another terminal: Start frontend
make frontend
```

Visit:
- ✅ Frontend: http://localhost:3000 (should show welcome page)
- ✅ Backend: http://localhost:8000 (should show JSON status)
- ✅ GraphQL: http://localhost:8000/graphql (should show playground)

**Checkpoint:** If all three URLs work, proceed. If not, check Docker is running and ports are free.

---

### Phase 2: Define Your Domain (1 hour)

#### 2.1 Replace Sample Models

Open `backend/src/db/models.py` and replace the sample models (Tenant, User, Asset) with your domain models.

**Example: Task Management App**

```python
"""Domain models for task management."""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(back_populates="owner", lazy="selectin")


class Project(Base, UUIDMixin, TimestampMixin):
    """Project model."""
    __tablename__ = "projects"

    owner_uuid: Mapped[UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="projects", lazy="selectin")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", lazy="selectin")


class Task(Base, UUIDMixin, TimestampMixin):
    """Task model."""
    __tablename__ = "tasks"

    project_uuid: Mapped[UUID] = mapped_column(ForeignKey("projects.uuid"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="todo", nullable=False)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks", lazy="selectin")
```

**Tips:**
- Start with 3-5 core models (you can add more later)
- Use UUID primary keys (UUIDMixin)
- Add timestamps (TimestampMixin)
- Use type hints: `Mapped[str]`, `Mapped[int]`, etc.
- Nullable fields: `Mapped[str | None]`
- Add indexes on foreign keys and frequently queried fields

#### 2.2 Update Model Imports

Edit `backend/src/db/__init__.py`:

```python
"""Database package."""
from .base import Base
from .models import User, Project, Task  # Update this line
from .session import AsyncSessionLocal, engine, get_session

__all__ = [
    "Base",
    "User",
    "Project",
    "Task",
    "AsyncSessionLocal",
    "engine",
    "get_session",
]
```

#### 2.3 Create Initial Migration

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Initial schema with users, projects, tasks"

# Review the migration in alembic/versions/
# Make sure it looks correct!

# Apply migration
alembic upgrade head
```

**Verify:**
```bash
# Connect to database
docker exec -it my-project-postgres psql -U postgres -d app

# List tables
\dt

# You should see: users, projects, tasks, alembic_version
```

---

### Phase 3: Build GraphQL API (45 minutes)

#### 3.1 Define GraphQL Types

Edit `backend/src/api/graphql/types.py`:

```python
"""GraphQL types."""
import strawberry
from uuid import UUID
from datetime import datetime


@strawberry.type
class User:
    """GraphQL type for User."""
    uuid: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Project:
    """GraphQL type for Project."""
    uuid: UUID
    owner_uuid: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Task:
    """GraphQL type for Task."""
    uuid: UUID
    project_uuid: UUID
    title: str
    description: str | None
    status: str
    completed: bool
    created_at: datetime
    updated_at: datetime


# Input types for mutations
@strawberry.input
class CreateProjectInput:
    """Input for creating a project."""
    owner_uuid: UUID
    name: str
    description: str | None = None


@strawberry.input
class CreateTaskInput:
    """Input for creating a task."""
    project_uuid: UUID
    title: str
    description: str | None = None
    status: str = "todo"
```

#### 3.2 Define Queries and Mutations

Edit `backend/src/api/graphql/schema.py`:

```python
"""GraphQL schema with queries and mutations."""
import strawberry
from uuid import UUID
from sqlalchemy import select

from .types import User, Project, Task, CreateProjectInput, CreateTaskInput
from ...db import models


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    async def users(self, info: strawberry.Info) -> list[User]:
        """Get all users."""
        session = info.context["session"]
        result = await session.execute(select(models.User))
        return [
            User(
                uuid=u.uuid,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in result.scalars()
        ]

    @strawberry.field
    async def projects(
        self,
        info: strawberry.Info,
        owner_uuid: UUID | None = None
    ) -> list[Project]:
        """Get projects, optionally filtered by owner."""
        session = info.context["session"]
        stmt = select(models.Project)
        if owner_uuid:
            stmt = stmt.where(models.Project.owner_uuid == owner_uuid)

        result = await session.execute(stmt)
        return [
            Project(
                uuid=p.uuid,
                owner_uuid=p.owner_uuid,
                name=p.name,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in result.scalars()
        ]

    @strawberry.field
    async def tasks(
        self,
        info: strawberry.Info,
        project_uuid: UUID | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """Get tasks with optional filters."""
        session = info.context["session"]
        stmt = select(models.Task)

        if project_uuid:
            stmt = stmt.where(models.Task.project_uuid == project_uuid)
        if status:
            stmt = stmt.where(models.Task.status == status)

        result = await session.execute(stmt)
        return [
            Task(
                uuid=t.uuid,
                project_uuid=t.project_uuid,
                title=t.title,
                description=t.description,
                status=t.status,
                completed=t.completed,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in result.scalars()
        ]


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    async def create_project(
        self,
        info: strawberry.Info,
        input: CreateProjectInput
    ) -> Project:
        """Create a new project."""
        session = info.context["session"]

        db_project = models.Project(
            owner_uuid=input.owner_uuid,
            name=input.name,
            description=input.description,
        )

        session.add(db_project)
        await session.flush()
        await session.refresh(db_project)

        return Project(
            uuid=db_project.uuid,
            owner_uuid=db_project.owner_uuid,
            name=db_project.name,
            description=db_project.description,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
        )

    @strawberry.mutation
    async def create_task(
        self,
        info: strawberry.Info,
        input: CreateTaskInput
    ) -> Task:
        """Create a new task."""
        session = info.context["session"]

        db_task = models.Task(
            project_uuid=input.project_uuid,
            title=input.title,
            description=input.description,
            status=input.status,
        )

        session.add(db_task)
        await session.flush()
        await session.refresh(db_task)

        return Task(
            uuid=db_task.uuid,
            project_uuid=db_task.project_uuid,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            completed=db_task.completed,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
        )


# Schema is already created at the bottom - no changes needed
schema = strawberry.Schema(query=Query, mutation=Mutation)
```

#### 3.3 Update Alembic Environment

Edit `backend/alembic/env.py` - update the imports:

```python
# Import Base and all models
from src.db.base import Base
from src.db.models import User, Project, Task  # Update this line
```

#### 3.4 Test GraphQL API

Restart backend:
```bash
# Stop backend (Ctrl+C)
# Restart
make backend
```

Visit http://localhost:8000/graphql and test:

```graphql
# Create a user first (you'll need to do this via Python or pgAdmin for now)
# Then test queries:

query GetProjects {
  projects {
    uuid
    name
    description
  }
}

query GetTasks {
  tasks {
    uuid
    title
    status
  }
}
```

---

### Phase 4: Build Frontend Pages (45 minutes)

#### 4.1 Generate TypeScript Types

```bash
cd frontend
npm run codegen
```

This creates `src/types/graphql.ts` with fully typed queries.

#### 4.2 Create Your First Page

Create `frontend/src/app/projects/page.tsx`:

```tsx
"use client";

import { useQuery, gql } from "@apollo/client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const GET_PROJECTS = gql`
  query GetProjects {
    projects {
      uuid
      name
      description
      createdAt
    }
  }
`;

interface Project {
  uuid: string;
  name: string;
  description: string | null;
  createdAt: string;
}

export default function ProjectsPage() {
  const { loading, error, data } = useQuery<{ projects: Project[] }>(GET_PROJECTS);

  if (loading) return <div className="p-24">Loading...</div>;
  if (error) return <div className="p-24">Error: {error.message}</div>;

  return (
    <main className="flex min-h-screen flex-col p-24">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Projects</h1>
            <p className="text-muted-foreground">Manage your projects</p>
          </div>
          <Button asChild variant="outline">
            <Link href="/">← Back</Link>
          </Button>
        </div>

        {data?.projects.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">
                No projects yet. Create one via the GraphQL API.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {data?.projects.map((project) => (
              <Card key={project.uuid}>
                <CardHeader>
                  <CardTitle>{project.name}</CardTitle>
                  <CardDescription>
                    {project.description || "No description"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Created {new Date(project.createdAt).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
```

#### 4.3 Update Home Page

Edit `frontend/src/app/page.tsx` to link to your new page:

```tsx
// Change the "View Tenants" button to "View Projects"
<Button asChild>
  <Link href="/projects">View Projects</Link>
</Button>
```

#### 4.4 Verify Frontend

Visit http://localhost:3000:
- ✅ Click "View Projects"
- ✅ Should see "No projects yet" or your projects if you created any

---

### Phase 5: Write First Tests (30 minutes)

#### 5.1 Test Your Models

Edit `backend/tests/test_models.py`:

```python
"""Test domain models."""
import pytest
from sqlalchemy import select
from src.db.models import User, Project, Task


@pytest.mark.asyncio
async def test_create_user(session):
    """Test creating a user."""
    user = User(
        email="test@example.com",
        full_name="Test User"
    )
    session.add(user)
    await session.commit()

    result = await session.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 1
    assert users[0].email == "test@example.com"


@pytest.mark.asyncio
async def test_create_project(session):
    """Test creating a project with user."""
    # Create user
    user = User(email="owner@example.com", full_name="Owner")
    session.add(user)
    await session.flush()

    # Create project
    project = Project(
        owner_uuid=user.uuid,
        name="Test Project",
        description="A test project"
    )
    session.add(project)
    await session.commit()

    # Verify
    result = await session.execute(select(Project))
    projects = result.scalars().all()
    assert len(projects) == 1
    assert projects[0].name == "Test Project"
    assert projects[0].owner_uuid == user.uuid


@pytest.mark.asyncio
async def test_create_task(session):
    """Test creating a task."""
    # Create user and project
    user = User(email="test@example.com", full_name="Test")
    session.add(user)
    await session.flush()

    project = Project(owner_uuid=user.uuid, name="Project")
    session.add(project)
    await session.flush()

    # Create task
    task = Task(
        project_uuid=project.uuid,
        title="Test Task",
        status="todo"
    )
    session.add(task)
    await session.commit()

    # Verify
    result = await session.execute(select(Task))
    tasks = result.scalars().all()
    assert len(tasks) == 1
    assert tasks[0].title == "Test Task"
    assert tasks[0].status == "todo"
    assert tasks[0].completed is False
```

#### 5.2 Run Tests

```bash
cd backend
pytest

# Should see all tests pass
```

---

### Phase 6: Initialize Git & Documentation (15 minutes)

#### 6.1 Initialize Git

```bash
git init
git add .
git commit -m "Initial commit - project bootstrap

- Set up FastAPI + GraphQL backend
- Set up Next.js + TypeScript frontend
- Add domain models: User, Project, Task
- Add GraphQL schema and resolvers
- Add basic tests
- Configure Docker Compose

🤖 Generated with Claude Code
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

#### 6.2 Update README

Edit `README.md` with your project specifics:

```markdown
# My Project Name

Brief description of what this does.

## Domain Model

- **User**: System users
- **Project**: User-owned projects
- **Task**: Tasks within projects

## Quick Start

\`\`\`bash
make init
make dev
\`\`\`

See [STACK.md](./STACK.md) for architecture decisions.
```

---

## Verification Checklist

Before moving to feature development, verify:

**Backend:**
- [ ] Models defined in `backend/src/db/models.py`
- [ ] Migration created and applied
- [ ] Can query database tables via psql
- [ ] GraphQL schema defined
- [ ] GraphQL playground works (http://localhost:8000/graphql)
- [ ] Can execute queries successfully
- [ ] Tests pass (`pytest`)

**Frontend:**
- [ ] Types generated (`npm run codegen`)
- [ ] At least one page created
- [ ] Page successfully queries backend
- [ ] No TypeScript errors (`npm run build`)

**DevOps:**
- [ ] Docker Compose starts all services
- [ ] Environment files configured
- [ ] Git repository initialized
- [ ] README updated

**If all checked, you're ready for feature development! 🎉**

---

## Next Steps

### Option 1: Sprint Workflow

Use the playbook sprint system:

```bash
/sprint-new "Add task creation UI"
/sprint-start 1
# Follow sprint workflow
```

### Option 2: Continue Building

Add features incrementally:
1. Authentication (see `patterns/authentication.md`)
2. More pages (tasks list, task detail)
3. Forms (create project, create task)
4. Real-time updates (WebSockets)

### Option 3: Deploy

See `cloud/deployment.md` for:
- AWS ECS deployment
- Environment setup
- CI/CD pipeline

---

## Troubleshooting

### Database Connection Failed

```bash
# Check Postgres is running
docker-compose ps

# Restart if needed
docker-compose restart postgres
```

### Migration Fails

```bash
# Check current version
alembic current

# Downgrade one step
alembic downgrade -1

# Try upgrade again
alembic upgrade head
```

### Frontend Can't Reach Backend

1. Check backend is running: http://localhost:8000/health
2. Check CORS in `backend/.env`: `CORS_ORIGINS=http://localhost:3000`
3. Check frontend env: `NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql`

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use make commands (they do this automatically)
make backend
make frontend
```

---

## Time Breakdown

- **Phase 0 (Planning):** 15 minutes
- **Phase 1 (Setup):** 30 minutes
- **Phase 2 (Domain):** 60 minutes
- **Phase 3 (GraphQL):** 45 minutes
- **Phase 4 (Frontend):** 45 minutes
- **Phase 5 (Tests):** 30 minutes
- **Phase 6 (Git/Docs):** 15 minutes

**Total:** ~4 hours first time, ~30 minutes once familiar

---

## Related Playbooks

- [Pattern Implementation Sequence](./pattern-implementation-sequence.md) - What order to add patterns
- [Development Sequence](../workflows/development-sequence.md) - Day-to-day workflow
- [Sprint Workflow v2](../workflows/sprint-workflow-v2.md) - Feature development process

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial version |
