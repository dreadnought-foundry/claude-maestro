# Recipe: Self-Hosted GitHub Actions Runner

**Category**: playbook
**Version**: 1.1
**Last Updated**: 2025-12-15
**Sprints**: Sprint 140, Sprint 141
**ADRs**:
- [ADR-051: Self-Hosted GitHub Runners](../../architecture/decisions/ADR-051-self-hosted-github-runners.md)
- [ADR-052: Native PostgreSQL for Mac Runner](../../architecture/decisions/ADR-052-native-postgresql-self-hosted-runner.md)

## Context

**When to use this recipe:**
- You're paying too much for GitHub Actions minutes
- You need unlimited CI/CD capacity
- You have spare hardware or can provision a cheap VPS
- You want faster builds with cached dependencies

**When NOT to use this recipe:**
- You have minimal CI/CD usage (under 2,000 minutes/month is free)
- You can't maintain infrastructure
- You need macOS runners but only have Linux

## Ingredients

Before starting, ensure you have:

- [ ] GitHub repository admin access
- [ ] A server: Mac Mini, Linux box, or VPS ($5-10/mo)
- [ ] SSH access to the server
- [ ] 30-60 minutes for setup

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                      GITHUB.COM                               │
│                                                               │
│  git push ──▶ Workflow triggered ──▶ Job added to queue      │
│                                              │                │
└──────────────────────────────────────────────┼────────────────┘
                                               │
                      HTTPS (outbound only)    │
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   YOUR RUNNER                                 │
│                                                               │
│  Runner polls: "Any jobs for me?" ◀──────────────────────────│
│        │                                                      │
│        ▼                                                      │
│  Clone ──▶ Run tests ──▶ Report back to GitHub               │
│                                                               │
│  [Your Mac / Linux / VPS - $0 to $10/mo]                     │
└──────────────────────────────────────────────────────────────┘
```

**Key insight**: The runner connects **outbound** to GitHub. No firewall changes needed!

## Quick Start: Mac Studio / Mac Mini / MacBook

If you're on macOS and just want it working in 5 minutes:

```bash
# 1. Create folder and download
mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-osx-arm64-2.311.0.tar.gz
tar xzf actions-runner.tar.gz

# 2. Get token: GitHub repo → Settings → Actions → Runners → New self-hosted runner
#    Copy the token shown

# 3. Configure
./config.sh --url https://github.com/YOUR-ORG/YOUR-REPO --token YOUR_TOKEN

# 4. Install as invisible background service
./svc.sh install
./svc.sh start

# Done! Runner is now running invisibly. Verify at:
# GitHub repo → Settings → Actions → Runners (should show green "Idle")
```

The runner uses ~50MB RAM when idle. You won't notice it.

---

## Mac PostgreSQL Optimization (Recommended)

If your project uses PostgreSQL with PostGIS, install it natively instead of using Docker. This avoids Rosetta x86 emulation and saves 60-90 seconds per CI job.

```bash
# Install PostgreSQL 17 and PostGIS (ARM native)
brew install postgresql@17 postgis

# Start as background service
brew services start postgresql@17

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Configure pg_hba.conf for trust authentication
PG_HBA="/opt/homebrew/var/postgresql@17/pg_hba.conf"
# Ensure local connections use 'trust' (check file, edit if needed)

# Create test database and user
createdb corrdata_test
createuser -s corrdata
psql -c "ALTER USER corrdata WITH PASSWORD 'corrdata_test';"

# Add extensions
psql -d corrdata_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d corrdata_test -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql -d corrdata_test -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

# Verify
psql -d corrdata_test -c "SELECT PostGIS_Version();"
```

**Why this is faster:**

| Docker PostGIS | Native PostgreSQL |
|----------------|-------------------|
| 30s container startup | 0s (already running) |
| 10s PostGIS init | 0s (pre-installed) |
| ~70% speed (Rosetta) | 100% speed (ARM) |
| **Total: 40-60s overhead** | **Total: <2s overhead** |

See [ADR-052](../../architecture/decisions/ADR-052-native-postgresql-self-hosted-runner.md) for details.

---

## Steps (Detailed)

### Step 1: Choose Your Runner Host

**Option A: Use your daily Mac (Mac Studio, MacBook, etc.)** ⭐ EASIEST
- Runner is a tiny background process (~50MB RAM when idle)
- Runs invisibly, doesn't interfere with your work
- Only uses CPU when builds are actually running
- If Mac sleeps, jobs queue and run when it wakes

**Option B: Use dedicated Mac Mini or Linux machine**
- Always online, 24/7 availability
- Good if you need builds to run overnight

**Option C: Provision a VPS** (most reliable)
```bash
# Hetzner (cheapest): €4.50/mo for 2 vCPU, 4GB RAM, 40GB SSD
# DigitalOcean: $6/mo for 1 vCPU, 1GB RAM, 25GB SSD
# Linode: $5/mo for 1 vCPU, 1GB RAM, 25GB SSD

# Create Ubuntu 22.04 LTS instance
# SSH in:
ssh root@YOUR_SERVER_IP
```

**Expected outcome**: SSH access to your server

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g pnpm

# Git
sudo apt install -y git

# PostgreSQL (for integration tests)
sudo apt install -y postgresql postgresql-contrib

# Optional: Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER

# Create runner user (don't run as root)
sudo useradd -m -s /bin/bash runner
sudo usermod -aG docker runner  # if using Docker
```

**Expected outcome**: All required tools installed

### Step 3: Get Runner Token from GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **Runners**
3. Click **New self-hosted runner**
4. Select your OS (Linux/macOS)
5. **Copy the token** shown (it expires in 1 hour!)

**Expected outcome**: A token like `AXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

### Step 4: Install GitHub Runner Application

```bash
# Switch to runner user
sudo su - runner

# Create directory
mkdir actions-runner && cd actions-runner

# Download runner (check GitHub for latest version)
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner.tar.gz

# Configure (use YOUR token from Step 3)
./config.sh --url https://github.com/YOUR-ORG/YOUR-REPO --token YOUR_TOKEN

# When prompted:
#   Runner name: [Enter] for default or give it a name
#   Labels: [Enter] for default
#   Work folder: [Enter] for default
```

**Expected outcome**: Configuration complete, runner registered

### Step 5: Install as System Service

```bash
# Exit runner user, back to root/sudo user
exit

# Install service
cd /home/runner/actions-runner
sudo ./svc.sh install runner

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

**Expected outcome**: Service running, will auto-start on boot

### Step 6: Verify in GitHub

1. Go back to **Settings** → **Actions** → **Runners**
2. Your runner should show as **Idle** (green dot)

**Expected outcome**: Runner shows online in GitHub

### Step 7: Update Your Workflows

```yaml
# .github/workflows/test.yml

# Change this:
jobs:
  test:
    runs-on: ubuntu-latest  # GitHub-hosted

# To this:
jobs:
  test:
    runs-on: self-hosted  # Your runner
```

**Expected outcome**: Workflows run on your infrastructure

## Verification

Push a change and watch the Actions tab:

```bash
git commit --allow-empty -m "test: verify self-hosted runner"
git push
```

Check the workflow run - it should show your runner name.

Expected output in Actions log:
```
Runner: your-runner-name
Operating System: Linux
Runner Image: self-hosted
```

## Advanced Configuration

### Add Labels for Multiple Runners

```bash
# During setup, or reconfigure:
./config.sh --labels linux,python,fast
```

Then in workflows:
```yaml
runs-on: [self-hosted, linux, python]
```

### Fallback to GitHub-Hosted

If your runner goes down, fall back automatically:

```yaml
jobs:
  test:
    runs-on: ${{ github.repository_owner == 'your-org' && 'self-hosted' || 'ubuntu-latest' }}
```

### Keep Runner Updated

```bash
# Check for updates periodically
cd /home/runner/actions-runner
./config.sh --check
```

## Learnings

### From Sprint 140
- Outbound-only connection makes firewall setup trivial
- VPS reliability is worth the $5-10/mo vs home hardware
- Cached dependencies make builds 2-3x faster than GitHub-hosted

## Anti-Patterns

### Don't: Run as Root

**What it looks like**: Installing and running the runner as root user

**Why it's bad**: Security risk - workflow code runs with root privileges

**Instead**: Create a dedicated `runner` user with minimal permissions

### Don't: Skip the Service Installation

**What it looks like**: Running `./run.sh` manually in a terminal

**Why it's bad**: Runner stops when you close the terminal or reboot

**Instead**: Always install as a service with `svc.sh install`

### Don't: Store Secrets on Runner

**What it looks like**: Putting API keys or credentials in files on the runner

**Why it's bad**: Workflows can read local files; security risk

**Instead**: Use GitHub Secrets, which are injected at runtime

## Cost Comparison

| Approach | Monthly Cost | Minutes |
|----------|-------------|---------|
| GitHub Actions (heavy use) | $40-100+ | Pay per minute |
| Self-hosted (VPS) | $5-10 | Unlimited |
| Self-hosted (existing hardware) | $0 | Unlimited |

## Related Recipes

- [Development Infrastructure](../workflows/development-infrastructure.md)
- [ADR-051: Self-Hosted GitHub Runners](../../architecture/decisions/ADR-051-self-hosted-github-runners.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-15 | Added native PostgreSQL optimization for Mac (ADR-052) |
| 1.0 | 2025-12-15 | Initial version |
