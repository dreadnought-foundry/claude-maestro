# Knowledge Base

Architecture patterns, operational playbooks, coding standards, and workflow documentation. Previously maintained in a separate `ai-playbook` repository, now unified here as the single source of truth.

## Contents

### [Patterns](./patterns/)
Reusable architecture recipes with code examples, anti-patterns, and verification steps.

| Pattern | Description |
|---------|-------------|
| [Provider Pattern](./patterns/provider-pattern.md) | Abstract AI/service providers with fallback |
| [Domain Model Layering](./patterns/domain-model-layering.md) | DB → Domain → API separation |
| [Three-Layer Database](./patterns/three-layer-database.md) | Schema, queries, domain conversion |
| [GraphQL Schema](./patterns/graphql-schema.md) | Schema design and resolver patterns |
| [MCP Tool Registry](./patterns/mcp-tool-registry.md) | Model Context Protocol integration |
| [Configuration Management](./patterns/configuration-management.md) | Environment and config patterns |
| [Session Factory Testing](./patterns/session-factory-testing.md) | Test isolation with factories |
| [Tech Stack Reference](./patterns/tech-stack-reference.md) | Technology selection guide |
| [Alert Engine](./patterns/alert-engine.md) | Event-driven alerting system |

### [Playbooks](./playbooks/)
Step-by-step operational guides for common development tasks.

| Playbook | Description |
|----------|-------------|
| [Project Bootstrap](./playbooks/project-bootstrap-guide.md) | Initialize a new project from scratch |
| [Deployment Setup](./playbooks/deployment-setup.md) | Configure deployment pipelines |
| [Adding External Data Source](./playbooks/adding-external-data-source.md) | Integrate third-party data |
| [Creating REST Endpoint](./playbooks/creating-rest-endpoint.md) | Build API endpoints |
| [Onboarding MCP Tool](./playbooks/onboarding-mcp-tool.md) | Add new MCP tools |
| [Pattern Implementation](./playbooks/pattern-implementation-sequence.md) | Order of pattern adoption |
| [Project Execution Lessons](./playbooks/project-execution-lessons.md) | Lessons from past projects |
| [Self-Hosted GitHub Runner](./playbooks/self-hosted-github-runner.md) | CI/CD runner setup |
| [v0 UI Generation](./playbooks/v0-ui-generation.md) | Using v0 for UI scaffolding |

### [Standards](./standards/)
Coding conventions and quality standards.

| Standard | Description |
|----------|-------------|
| [Coding Standards](./standards/coding-standards.md) | General coding conventions |

### [Workflows](./workflows/)
Process documentation for recurring development activities.

| Workflow | Description |
|----------|-------------|
| [Sprint Workflow v2](./workflows/sprint-workflow-v2.md) | Full sprint lifecycle process |
| [Development Sequence](./workflows/development-sequence.md) | Order of operations for features |
| [Database Migrations](./workflows/database-migrations.md) | Schema change process |
| [Postmortem Process](./workflows/postmortem-process.md) | Sprint retrospective format |
| [Documentation Approach](./workflows/documentation-approach.md) | How we document things |
| [Development Infrastructure](./workflows/development-infrastructure.md) | Local dev environment setup |
| [VS Code Setup](./workflows/vscode-setup.md) | Editor configuration |

### [Cloud](./cloud/)
Infrastructure and deployment guides.

| Guide | Description |
|-------|-------------|
| [AWS Infrastructure](./cloud/aws-infrastructure.md) | ECS/Fargate deployment |

### [Mobile](./mobile/)
Mobile application guides.

| Guide | Description |
|-------|-------------|
| [App Store Setup](./mobile/app-store-setup-guide.md) | iOS/Android store configuration |

### Other

| File | Description |
|------|-------------|
| [ADR Synthesis](./ADR-SYNTHESIS.md) | 49 architecture decision records |
| [CLAUDE.md Template](./CLAUDE.md.template) | Template for project instructions |
| [Sprint Template](./_TEMPLATE.md) | Template for new sprint files |
| [Seed Data Service](./seed-data-service.md) | Test data generation patterns |
