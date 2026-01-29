# Vision: Maestro + Auto-Claude Integration

**The Conductor and the Orchestra**

---

## The One-Sentence Vision

**You define WHAT gets built and HOW GOOD it needs to be (Maestro), while Auto-Claude figures out WHO builds it and executes autonomously (Auto-Claude).**

---

## The Problem Today

### Using Auto-Claude Alone

You write a spec, Auto-Claude spins up agents, they build autonomously. But:

- A research spike gets held to the same 75% coverage as production code → **false failures**
- Agents skip from planning to coding without your approval → **surprise architectures**
- Work completes but learnings aren't captured → **repeat mistakes**
- No visibility into what phase work is in → **"is it done yet?"**

### Using Maestro Alone

You get structured workflows, quality gates, postmortems. But:

- Single Claude session does all the work → **slow**
- No parallel execution → **bottleneck**
- Manual step progression → **babysitting required**

---

## The Integrated Future

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOU                                      │
│                          │                                       │
│            "Build a user notification system"                    │
│            "This is a backend sprint, 85% coverage"              │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      MAESTRO                               │  │
│  │                  (The Conductor)                           │  │
│  │                                                            │  │
│  │  • Defines the sprint and quality requirements             │  │
│  │  • Sets coverage threshold (85% for backend)               │  │
│  │  • Tracks workflow phases (planning → building → done)     │  │
│  │  • Enforces quality gates before completion                │  │
│  │  • Generates postmortem and captures learnings             │  │
│  │  • Organizes work into epics/sprints                       │  │
│  │                                                            │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                    │
│                    "Execute this sprint"                         │
│                             │                                    │
│                             ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    AUTO-CLAUDE                             │  │
│  │                  (The Orchestra)                           │  │
│  │                                                            │  │
│  │  • Spins up parallel agents in isolated worktrees          │  │
│  │  • Agents autonomously implement the sprint                │  │
│  │  • Handles merge conflicts between agents                  │  │
│  │  • Reports progress back to Maestro                        │  │
│  │  • Submits work for Maestro quality gate approval          │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## A Day in Your Life (Integrated Workflow)

### Morning: Define the Work

```bash
# In your terminal, you create a new sprint using Maestro
/sprint-new "User notification system" --type=backend --epic=3

# Maestro creates:
# - docs/sprints/1-todo/sprint-42_user-notification-system/
# - Sprint file with 85% coverage requirement (backend type)
# - Registry entry linking to Epic 3
```

You open the sprint file and fill in the requirements:
- What the notification system should do
- Which models/APIs are needed
- Acceptance criteria

### Mid-Morning: Launch Execution

```bash
# You're happy with the sprint definition, so you start it
/sprint-start 42

# This does TWO things:
# 1. Maestro: Creates state file, moves sprint to "in-progress"
# 2. Auto-Claude: Receives the sprint, begins autonomous execution
```

**What happens next (without you):**

1. Auto-Claude reads the sprint file
2. Creates a plan and spins up 3 agents in parallel:
   - Agent 1: Database models + migrations
   - Agent 2: API endpoints
   - Agent 3: Test suite
3. Agents work in isolated git worktrees
4. Auto-Claude reports phase transitions back to Maestro

### Lunch: Check Progress

```bash
# You want to see where things are
/sprint-status

# Output:
# Sprint 42: User Notification System
# Type: backend (85% coverage required)
#
# Maestro Phase: 2.3 - Implementation
# Auto-Claude Status: 3 agents active
#   - Agent 1: models complete, migrations running
#   - Agent 2: 4/6 endpoints done
#   - Agent 3: 12 tests written, waiting for endpoints
#
# Estimated: 2 more cycles until QA phase
```

You didn't have to do anything. It's just running.

### Afternoon: Quality Gate

Auto-Claude finishes implementation and submits to Maestro's quality gate:

```
┌─────────────────────────────────────────────────────────────┐
│              MAESTRO QUALITY GATE - Sprint 42               │
├─────────────────────────────────────────────────────────────┤
│ Sprint Type: backend                                        │
│ Coverage Required: 85%                                      │
│ Coverage Actual: 87% ✓                                      │
├─────────────────────────────────────────────────────────────┤
│ Pre-Flight Checklist:                                       │
│ [✓] All tests pass (47 passed, 0 failed)                   │
│ [✓] Coverage meets threshold (87% >= 85%)                  │
│ [✓] No lint errors                                         │
│ [✓] No type errors                                         │
│ [✓] Migrations valid and reversible                        │
│ [✓] No debug statements in code                            │
│ [✓] No secrets in code                                     │
│ [✗] Documentation not updated                              │
│ [✓] Changelog updated                                      │
├─────────────────────────────────────────────────────────────┤
│ BLOCKED: 1 checklist item failed                           │
│ Auto-Claude will attempt to fix...                         │
└─────────────────────────────────────────────────────────────┘
```

Auto-Claude automatically addresses the documentation gap, then resubmits:

```
MAESTRO QUALITY GATE - Sprint 42: PASSED ✓
Proceeding to merge phase...
```

### End of Day: Completion

```bash
# Auto-Claude finished and merged. You complete the sprint:
/sprint-complete 42

# Maestro:
# 1. Generates postmortem with agent metrics
# 2. Moves sprint to done (with --done suffix)
# 3. Updates registry
# 4. Creates git tag
# 5. Checks if Epic 3 is now complete
```

**Generated Postmortem:**

```markdown
## Sprint 42 Postmortem: User Notification System

### Summary
| Metric | Value |
|--------|-------|
| Duration | 4.2 hours |
| Agents Used | 3 |
| Tests Added | 47 |
| Coverage | 87% (+12% from baseline) |
| Files Changed | 23 |
| Rework Cycles | 1 (documentation fix) |

### Agent Contributions
| Agent | Task | Files | Time |
|-------|------|-------|------|
| Agent 1 | Models + Migrations | 8 | 1.1h |
| Agent 2 | API Endpoints | 11 | 2.4h |
| Agent 3 | Test Suite | 4 | 0.7h |

### What Went Well
- Parallel agent execution reduced total time by ~60%
- Migration validation caught a missing index

### What Could Improve
- Documentation should be written alongside code, not after

### Patterns Discovered
- Notification preference model reusable for other user settings

### Learnings
- Backend sprints benefit from dedicated test agent
```

---

## The Control Model

### What YOU Control (via Maestro)

| Control | How |
|---------|-----|
| **What gets built** | Write sprint requirements |
| **Quality bar** | Set sprint type (backend=85%, spike=0%) |
| **Work organization** | Group sprints into epics |
| **When to start** | `/sprint-start` |
| **When it's done** | `/sprint-complete` |
| **Checkpoints** | Optional phase approvals |

### What AUTO-CLAUDE Controls

| Control | How |
|---------|-----|
| **How many agents** | Based on sprint complexity |
| **Which agent does what** | Task decomposition |
| **Execution order** | Dependency analysis |
| **Conflict resolution** | AI-powered merge |
| **Retry on failure** | Automatic rework |

### The Handoff Points

```
YOU ──────────────────────────────────────────────────────────► YOU
 │                                                               │
 │  Define    Start                              Complete   Review
 │  Sprint    Sprint                             Sprint     Postmortem
 │    │         │                                  │          │
 │    ▼         ▼                                  ▼          ▼
 │ ┌─────┐  ┌──────┐                          ┌──────┐  ┌─────────┐
 │ │Write│  │Maestro│                         │Maestro│  │Learnings│
 │ │Spec │  │ Init  │                         │ Gate  │  │Captured │
 │ └──┬──┘  └───┬───┘                         └───┬───┘  └─────────┘
 │    │         │                                 │
 │    │         ▼                                 ▲
 │    │    ┌─────────────────────────────────────┐│
 │    └───►│           AUTO-CLAUDE               ││
 │         │  (Autonomous execution happens here)├┘
 │         │   - Plan decomposition              │
 │         │   - Agent spawning                  │
 │         │   - Parallel implementation         │
 │         │   - Testing & validation            │
 │         │   - Merge & conflict resolution     │
 │         └─────────────────────────────────────┘
 │
 │  YOUR INVOLVEMENT: ~10 minutes
 │  AUTO-CLAUDE WORK: ~4 hours (example)
```

---

## Different Sprint Types, Different Experiences

### Backend Sprint (High Rigor)

```yaml
type: backend
coverage: 85%
```

- Maestro enforces integration tests
- Quality gate is strict
- Full postmortem generated
- **Use for**: Core services, APIs, data layer

### Research Sprint (Documentation Focus)

```yaml
type: research
coverage: 30%
```

- Maestro requires documentation, relaxes coverage
- Auto-Claude focuses on exploration, not production code
- Postmortem emphasizes learnings over metrics
- **Use for**: Spikes, investigations, POCs

### Spike Sprint (Minimal Gates)

```yaml
type: spike
coverage: 0%
```

- Maestro only checks for documentation
- Auto-Claude runs fast without test overhead
- Quick postmortem, pattern extraction only
- **Use for**: Quick experiments, throwaway code

---

## What Changes From Today

### If You Currently Use Auto-Claude

| Before | After |
|--------|-------|
| Write spec, hope coverage is enough | Declare sprint type, know the bar |
| Work completes, you move on | Postmortem captures learnings |
| Rerun failed builds manually | Quality gate blocks, Auto-Claude fixes |
| All work treated the same | Type-appropriate rigor |

### If You Currently Use Maestro

| Before | After |
|--------|-------|
| Single session, sequential work | Parallel agents, faster completion |
| Manual `/sprint-next` progression | Autonomous execution between gates |
| You implement the code | Auto-Claude implements, you review |
| Babysit each phase | Check in when notified |

---

## The Value Proposition

### For Speed

- **Before**: 8 hours of your time implementing a sprint
- **After**: 10 minutes defining + 10 minutes reviewing = **20 minutes of your time**

### For Quality

- **Before**: Coverage varies, sometimes 40%, sometimes 90%
- **After**: Type-appropriate coverage enforced automatically

### For Learning

- **Before**: Finish sprint, move on, forget
- **After**: Every sprint generates searchable postmortem with patterns

### For Control

- **Before (Auto-Claude alone)**: "I hope it's building what I wanted"
- **After**: Maestro enforces your quality requirements before merge

---

## Summary

| Layer | Role | You Interact Via |
|-------|------|------------------|
| **You** | Define work, set standards, review results | Sprint files, slash commands |
| **Maestro** | Enforce quality, track phases, capture learnings | Automatic (quality gate, postmortems) |
| **Auto-Claude** | Execute work with parallel agents | Automatic (runs autonomously) |

**The bottom line**: You stay in control of WHAT and HOW GOOD. Auto-Claude handles the HOW and WHO. Maestro is the contract between you and the machines.

---

## Appendix: Command Cheat Sheet

```bash
# Define work (Maestro)
/sprint-new "Title" --type=backend --epic=N
/epic-new "Epic Title"

# Execute work (triggers Auto-Claude)
/sprint-start <N>

# Monitor (Maestro + Auto-Claude status)
/sprint-status
/epic-status <N>

# Complete (Maestro finalizes)
/sprint-complete <N>

# Review learnings
/sprint-analytics
/epic-list
```

---

## Appendix: Architecture Summary

```
┌──────────────────────────────────────────────────────────────┐
│                      YOUR REPOSITORY                          │
│                                                               │
│  docs/sprints/                    .auto-claude/               │
│  ├── registry.json  ◄──────────►  ├── specs/                 │
│  ├── 1-todo/                      ├── worktrees/             │
│  ├── 2-in-progress/               └── state/                 │
│  └── 3-done/                                                 │
│       │                                  │                    │
│       │         ┌────────────────────────┘                    │
│       │         │                                             │
│       ▼         ▼                                             │
│  .claude/sprint-state.json  ◄───► Auto-Claude execution      │
│  (Maestro workflow state)         (parallel agents)          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```
