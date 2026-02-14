# Recipe: AWS Infrastructure Setup

**Category**: cloud
**Version**: 1.0
**Last Updated**: 2025-12-13
**Sprints**: Sprint 45, 62, 66, 68

## Context

**When to use this recipe:**
- Setting up a new AWS environment (staging/production)
- Deploying CorrData to EC2 instances
- Configuring AWS services (Cognito, CloudWatch, ECR)

**When NOT to use this recipe:**
- Local development (use docker-compose.yml instead)
- Non-AWS cloud providers

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CorrData AWS Architecture                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Region: us-west-1 (N. California) - See ADR-042                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  EC2 Instance (t3.medium or larger)                            │     │
│  │                                                                 │     │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ │     │
│  │  │ Nginx   │ │ API     │ │ Frontend │ │ Postgres│ │ Neo4j   │ │     │
│  │  │ :80/443 │ │ :8000   │ │ :3000    │ │ :5432   │ │ :7687   │ │     │
│  │  └────┬────┘ └────┬────┘ └────┬─────┘ └────┬────┘ └────┬────┘ │     │
│  │       │           │           │            │           │       │     │
│  │       └───────────┴───────────┴────────────┴───────────┘       │     │
│  │                    Docker Network                               │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │    ECR       │ │   Cognito    │ │  CloudWatch  │ │     S3       │   │
│  │ (Container   │ │ (Auth)       │ │ (Logs/       │ │ (Assets)     │   │
│  │  Registry)   │ │              │ │  Metrics)    │ │              │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Ingredients

Before starting, ensure you have:

- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI configured (`aws configure`)
- [ ] Docker installed locally
- [ ] SSH key pair for EC2 access
- [ ] Domain name (e.g., staging.corrdata.ai)
- [ ] SSL certificate (Let's Encrypt or ACM)

## Infrastructure Files Reference

All infrastructure files are in `infra/ec2-staging/`:

| File | Purpose |
|------|---------|
| `docker-compose.staging.yml` | Full stack deployment |
| `docker-compose.prod.yml` | Production deployment |
| `docker-compose.api-only.yml` | API-only deployment |
| `.env.example` | Environment variables template |
| `.env.staging.example` | Staging-specific variables |
| `init-db.sql` | Database initialization |
| `nginx/nginx-staging.conf` | Nginx reverse proxy config |
| `nginx/nginx-api-ssl.conf` | API-only with SSL |
| `cloudwatch-agent-config.json` | CloudWatch agent setup |
| `setup-cloudwatch-agent.sh` | CloudWatch installation script |

## Steps

### Step 1: Set Up ECR Repository

```bash
# Create ECR repositories
aws ecr create-repository --repository-name corrdata-api --region us-west-1
aws ecr create-repository --repository-name corrdata-frontend --region us-west-1

# Login to ECR
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 340646328578.dkr.ecr.us-west-1.amazonaws.com

# Build and push images
docker build -t corrdata-api -f Dockerfile.api .
docker tag corrdata-api:latest 340646328578.dkr.ecr.us-west-1.amazonaws.com/corrdata-api:staging
docker push 340646328578.dkr.ecr.us-west-1.amazonaws.com/corrdata-api:staging
```

### Step 2: Launch EC2 Instance

**Recommended specs:**
- **Instance type**: t3.medium (staging) or t3.large (production)
- **AMI**: Amazon Linux 2023
- **Storage**: 50GB gp3 SSD
- **Security Group**: Allow ports 22, 80, 443

```bash
# Connect to instance
ssh -i ~/.ssh/corrdata-key.pem ec2-user@<instance-ip>

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for docker group
exit
```

### Step 3: Configure Environment

```bash
# Create deployment directory
mkdir -p /opt/corrdata
cd /opt/corrdata

# Copy infrastructure files
scp -i ~/.ssh/corrdata-key.pem -r infra/ec2-staging/* ec2-user@<instance-ip>:/opt/corrdata/

# On EC2: Create .env from template
cp .env.staging.example .env

# Edit with your values
nano .env
```

**Required environment variables:**
```bash
# Database
DB_PASSWORD=<generate-secure-password>

# Neo4j
NEO4J_PASSWORD=<generate-secure-password>

# JWT
JWT_SECRET_KEY=<openssl rand -hex 32>
JWT_REFRESH_SECRET_KEY=<openssl rand -hex 32>

# Domain
DOMAIN=staging.corrdata.ai

# AWS Cognito (from Sprint 45)
COGNITO_USER_POOL_ID=us-west-1_XXXXXXXXX
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
COGNITO_DOMAIN=corrdata-staging

# Sentry (from Sprint 78)
SENTRY_API_DSN=https://xxx@sentry.io/xxx
SENTRY_WEB_DSN=https://xxx@sentry.io/xxx
```

### Step 4: Set Up SSL Certificates

```bash
# Install certbot
sudo yum install -y certbot

# Get certificate (stop nginx first if running)
sudo certbot certonly --standalone -d staging.corrdata.ai

# Certificate will be at:
# /etc/letsencrypt/live/staging.corrdata.ai/fullchain.pem
# /etc/letsencrypt/live/staging.corrdata.ai/privkey.pem
```

### Step 5: Deploy Services

```bash
cd /opt/corrdata

# Login to ECR
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 340646328578.dkr.ecr.us-west-1.amazonaws.com

# Pull latest images
docker-compose -f docker-compose.staging.yml pull

# Start services
docker-compose -f docker-compose.staging.yml up -d

# Check status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f api
```

### Step 6: Set Up CloudWatch Monitoring

```bash
# Run the setup script
chmod +x setup-cloudwatch-agent.sh
./setup-cloudwatch-agent.sh

# Verify agent is running
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status
```

**CloudWatch will collect:**
- Container metrics (CPU, memory)
- Application logs
- Nginx access/error logs
- System metrics

### Step 7: Run Database Migrations

```bash
# Enter API container
docker exec -it corrdata-staging-api bash

# Run migrations
cd /app
alembic upgrade head

# Verify
alembic current
```

## Verification

```bash
# Check all services are healthy
docker-compose -f docker-compose.staging.yml ps

# Test API health
curl https://staging.corrdata.ai/health

# Test GraphQL
curl -X POST https://staging.corrdata.ai/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'

# Check CloudWatch logs (AWS Console)
# Navigate to: CloudWatch > Log groups > corrdata/api
```

## Learnings

### From Sprint 45 (Cognito Setup)
- Cognito user pool must be in us-west-1 to match region
- Lambda triggers need proper IAM roles

### From Sprint 66 (Migration)
- Always backup database before migration
- Test migrations on staging first

### From Sprint 68 (CloudWatch)
- CloudWatch agent requires IAM role with CloudWatchAgentServerPolicy
- Log retention should be set to control costs

## Anti-Patterns

### Don't: Hard-code secrets in docker-compose

**What it looks like**: Putting passwords directly in YAML files

**Why it's bad**: Secrets get committed to git

**Instead**: Use .env files (gitignored) and environment variables

---

### Don't: Skip health checks

**What it looks like**: Removing healthcheck blocks from services

**Why it's bad**: No way to know if services are actually healthy

**Instead**: Keep health checks, they enable proper dependency ordering

---

### Don't: Use default Neo4j memory settings

**What it looks like**: Not setting heap/pagecache sizes

**Why it's bad**: Neo4j will consume all available memory

**Instead**: Set explicit memory limits based on instance size

## Variations

### For Production

Use `docker-compose.prod.yml` with:
- Larger memory allocations
- Multi-instance deployment
- Stricter security groups
- RDS instead of container PostgreSQL (optional)

### For API-Only Deployment

Use `docker-compose.api-only.yml` when:
- Frontend is hosted separately (Vercel)
- Only need backend services

## Related ADRs

- [ADR-042: AWS Infrastructure Configuration](../../architecture/decisions/ADR-042-aws-infrastructure-configuration.md) - Region and naming
- [ADR-040: AWS Native Observability](../../architecture/decisions/ADR-040-aws-native-observability.md) - CloudWatch setup
- [ADR-043: AWS Services Strategy](../../architecture/decisions/ADR-043-aws-services-strategy.md) - Service selection

## Related Sprints

- Sprint 45: AWS Cognito Authentication
- Sprint 62: AWS Account Setup
- Sprint 66: AWS Migration Finalization
- Sprint 68: AWS Services Integration

## Scripts Reference

### Deploy Script (deploy.sh)

```bash
#!/bin/bash
# Deploy CorrData to staging
set -e

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-staging}

echo "Deploying CorrData to $ENVIRONMENT with tag $IMAGE_TAG"

# Login to ECR
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin 340646328578.dkr.ecr.us-west-1.amazonaws.com

# Pull latest images
export IMAGE_TAG=$IMAGE_TAG
docker-compose -f docker-compose.$ENVIRONMENT.yml pull

# Deploy
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d

# Wait for health
sleep 30
curl -f http://localhost:8000/health || exit 1

echo "Deployment complete!"
```

### Rollback Script (rollback.sh)

```bash
#!/bin/bash
# Rollback to previous version
set -e

PREVIOUS_TAG=${1:-$(docker images --format "{{.Tag}}" | grep -v latest | head -2 | tail -1)}

echo "Rolling back to $PREVIOUS_TAG"

export IMAGE_TAG=$PREVIOUS_TAG
docker-compose -f docker-compose.staging.yml up -d

echo "Rollback complete"
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial AWS infrastructure playbook |
