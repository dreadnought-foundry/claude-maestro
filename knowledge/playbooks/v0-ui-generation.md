# v0.dev UI Generation Playbook

A step-by-step guide for using v0.dev to rapidly generate production-quality React components from UI specifications.

## Context

**When to use this playbook:**
- Starting a new web application or major UI feature
- Need to generate multiple pages/components quickly
- Want production-ready React + Tailwind + shadcn/ui code
- Prefer code-first over traditional wireframing

**Related resources:**
- **ADR**: [ADR-047: v0.dev AI-Assisted UI Generation](../../architecture/decisions/ADR-047-v0-dev-ui-generation.md)
- **Prompt Template**: [docs/ui/v0-dev-prompt.md](../../ui/v0-dev-prompt.md) (CorrData's full spec)
- **Workflow Guide**: [docs/guides/v0-dev-workflow-guide.md](../../guides/v0-dev-workflow-guide.md) (detailed reference)

## Why v0.dev?

| Traditional Approach | v0.dev Workflow |
|---------------------|-----------------|
| Days designing mockups | Hours writing specs |
| Weeks coding UI | Minutes generating |
| Multiple design tools | One spec document |
| Designer → Developer handoff | Direct to code |

v0.dev generates our exact stack: React 18 + TypeScript + Tailwind CSS + shadcn/ui.

## Ingredients

Before starting, you need:

- [ ] v0.dev account (free tier works)
- [ ] React project with Tailwind CSS and shadcn/ui installed
- [ ] Clear understanding of your features and user personas
- [ ] Basic wireframes or sketches (even hand-drawn work)

## The Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    v0.dev GENERATION WORKFLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   PREPARE              GENERATE            INTEGRATE             │
│   ┌─────────────────┐  ┌─────────────────┐ ┌─────────────────┐  │
│   │ 1. Write UI Spec│  │ 3. Upload to v0 │ │ 5. Export Code  │  │
│   │ 2. Define       │→ │ 4. Prompt by    │→│ 6. Adapt & Fix  │  │
│   │    Personas     │  │    Section      │ │ 7. Connect Data │  │
│   └─────────────────┘  └─────────────────┘ └─────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Create Your UI Specification

### Step 1.1: Document Structure

Create a markdown file with this structure:

```markdown
# [App Name] UI Generation Prompt for v0.dev

## Application Overview
Brief description, tech stack, key features

## User Personas
Who uses the app and what they need

## Information Architecture
Navigation structure, page hierarchy

## Page Specifications
Detailed wireframes for each page (use ASCII art)

## Component Patterns
Reusable patterns across the app

## Design System
Colors, typography, spacing
```

### Step 1.2: Define User Personas

For each persona, document:

```markdown
### Field Technician (Mobile-First)
- **Role:** Collects data in the field
- **Goal:** Record readings quickly and accurately
- **Key views:** Work orders, reading entry, QR scanner
- **Needs:** Large touch targets, offline capability, GPS capture
```

### Step 1.3: Create ASCII Wireframes

v0.dev interprets ASCII art extremely well:

```markdown
**Route:** `/dashboard`

**Layout:**
┌─────────────────────────────────────────────────────────────────┐
│ Dashboard                                        [Sync ●] [👤]  │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ KPI Card 1  │ │ KPI Card 2  │ │ KPI Card 3  │ │ KPI Card 4  │ │
│ │   42        │ │   98%       │ │   156       │ │   3         │ │
│ │ Active WOs  │ │ Compliance  │ │ Assets      │ │ Alerts      │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────┐ ┌───────────────────────────────┐ │
│ │ Recent Alerts             │ │ Upcoming Deadlines            │ │
│ │ • Alert 1 [Critical]      │ │ • Dec 15 - Monthly Report     │ │
│ │ • Alert 2 [Warning]       │ │ • Dec 20 - Inspection Due     │ │
│ └───────────────────────────┘ └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1.4: Specify Responsive Behavior

Always include how components adapt:

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Mobile | < 640px | Single column, bottom nav, card stacks |
| Tablet | 640-1024px | Collapsible sidebar, 2 columns |
| Desktop | > 1024px | Fixed sidebar, multi-column, data tables |

---

## Phase 2: Generate in v0.dev

### Step 2.1: Create Project

1. Go to [v0.dev](https://v0.dev)
2. Sign in and click **"New Project"**
3. Name it after your app

### Step 2.2: Upload Your Specification

1. Open your project
2. Click **"+"** and paste your UI spec document
3. v0.dev will use this as context for all chats

### Step 2.3: Generate Section by Section

**DO THIS:**
```
Chat 1: "Generate the sidebar navigation from section Navigation Structure"
Chat 2: "Generate the dashboard page from section 1. DASHBOARD"
Chat 3: "Generate the asset list table from section 2. ASSETS"
```

**NOT THIS:**
```
Chat 1: "Generate my entire application"  ← Too complex, poor results
```

### Step 2.4: Generation Order

Build from foundation to features:

```
LAYER 1: Foundation
├── Theme/Design tokens
├── App shell/Layout
└── Navigation components

LAYER 2: Core Pages
├── Dashboard
├── List views (tables/cards)
└── Detail views

LAYER 3: Forms & Inputs
├── Create/Edit forms
├── Search & filters
└── Data entry

LAYER 4: Specialized
├── Maps/Charts
├── Modals/Dialogs
└── Mobile-specific
```

---

## Phase 3: Export and Integrate

### Two Integration Methods

| Method | Best For |
|--------|----------|
| **ZIP Export** | Initial setup, major updates (5+ components) |
| **v0 CLI** | Adding single components after base is established |

### Method 1: ZIP Export

1. In v0.dev, click **Download** → **Download ZIP**
2. Save to your Downloads folder
3. Share path with Claude Code:

```
Here's the v0.dev export: ~/Downloads/my-project.zip

I added:
- Dashboard with KPI cards
- Asset list page with filters
- Sidebar navigation

Please integrate these new components.
```

Claude Code will:
- Extract and compare against existing project
- Copy only new/changed files
- Fix import paths for your project structure
- Install missing dependencies
- Verify build passes

### Method 2: v0 CLI (Single Components)

After base is established:

```bash
cd packages/web-app

# Get block ID from v0.dev URL: v0.dev/t/abc123xyz
pnpm v0 add abc123xyz

# Or add shadcn/ui components directly
pnpm v0 add dialog
pnpm v0 add data-table
```

### Step 3.1: Adapt Generated Code

v0.dev generates with mock data. Connect to your data layer:

```tsx
// BEFORE (v0.dev generated)
const assets = [
  { id: 1, name: "Asset 1", status: "active" },
];

// AFTER (connected to GraphQL)
import { useQuery } from '@apollo/client';
import { GET_ASSETS } from '@/graphql/queries';

const { data, loading } = useQuery(GET_ASSETS);
const assets = data?.assets ?? [];
```

---

## Prompt Templates

### Layout/Shell

```
Generate the main application layout with:

1. Collapsible sidebar (280px) with navigation from "Navigation Structure"
2. Top header with breadcrumbs, sync status, user menu
3. Bottom navigation bar for mobile (< 640px)
4. Support dark mode toggle

Use shadcn/ui Sheet for mobile menu.
```

### List Page

```
Generate a [entity] list page at route /[route] with:

1. Data table with columns: [list columns]
2. Filter controls: [list filters]
3. Search functionality
4. Bulk actions: [list actions]
5. Mobile layout: card stack with swipe actions

Include loading and empty states.
Refer to section "[X]" in my wireframes.
```

### Detail Page

```
Generate a [entity] detail page at route /[route]/[id] with:

1. Header with title and action buttons
2. Tab navigation: [list tabs]
3. Content sections: [describe each]
4. Mobile: tabs become vertical accordion

Refer to section "[X]" in my wireframes.
```

### Form

```
Generate a [create/edit] form for [entity] with:

1. Fields: [list all fields with types]
2. Validation: [describe rules]
3. Submit behavior: [what happens]
4. Mobile: large inputs, step-by-step wizard

Include error states and loading indicator.
```

---

## Best Practices

### Do's

| Practice | Why |
|----------|-----|
| Write detailed specs first | Better generation results |
| Use ASCII wireframes | v0.dev interprets them well |
| One component per chat | Focused, higher quality output |
| Iterate in same chat | "Make the button larger" works |
| Export frequently | Save good generations immediately |
| Reference your document | "As shown in section X" |

### Don'ts

| Avoid | Why |
|-------|-----|
| Generating entire app at once | Too complex, poor results |
| Vague prompts | "Make it pretty" doesn't help |
| Skipping the spec document | You'll get generic UI |
| Ignoring responsive | Always specify mobile behavior |
| Using generated code as-is | Always review and connect data |

---

## Sprint-Based Approach

For large projects, use **two paired sprints**:

```
┌─────────────────────────────────────────────────────────────────┐
│              PAIRED SPRINTS: SPEC + IMPLEMENTATION               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SPRINT N: Specification         SPRINT N+1: Implementation    │
│   ┌─────────────────────┐         ┌─────────────────────┐       │
│   │ CREATE THE PROMPT   │         │ BUILD FROM PROMPT   │       │
│   │                     │         │                     │       │
│   │ • User personas     │   →     │ • Generate in v0    │       │
│   │ • Page wireframes   │         │ • Export ZIP        │       │
│   │ • Design system     │         │ • Integrate code    │       │
│   │ • Component specs   │         │ • Connect data      │       │
│   └─────────────────────┘         └─────────────────────┘       │
│                                                                  │
│   Output: v0-dev-prompt.md        Output: Working UI pages      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Sprint N: Specification

**Deliverables:**
- Master prompt document with all page wireframes
- User personas with key workflows
- Design system tokens and patterns

### Sprint N+1: Implementation

**Workflow:**
1. Work section-by-section through the prompt
2. Generate pages in v0.dev
3. Export ZIP when section complete
4. Claude Code integrates via diff
5. Mark section complete, move to next

---

## CorrData Example

**What we built:**
- 11 user personas (office + field workers)
- 52 pages generated via v0.dev
- PWA with offline support
- Desktop and mobile responsive

**Sprints used:**
| Sprint | Title | Output |
|--------|-------|--------|
| Sprint 50 | UI Wireframes | `docs/ui/v0-dev-prompt.md` |
| Sprint 51 | UI Implementation | 52 working pages |

**Files integrated:**
| Category | Count | Location |
|----------|-------|----------|
| UI Components | 57 | `src/components/ui/` |
| Dashboard | 5 | `src/components/dashboard/` |
| Layout | 7 | `src/components/layout/` |
| Hooks | 2 | `src/hooks/` |

---

## Learnings

### What Worked Well
- ASCII wireframes in prompts produced accurate layouts
- One component per chat = higher quality output
- Iterating in same chat ("make it smaller") works great
- ZIP export + Claude Code diff = efficient integration

### What to Improve
- Always test responsive behavior before export
- Document design tokens upfront (colors, spacing)
- Plan mobile navigation from the start

### Anti-Patterns

**Don't: Generate Everything at Once**
- v0.dev works best with focused prompts
- Break large apps into logical sections

**Don't: Skip the Spec Document**
- Generic prompts → generic UI
- Detailed specs → tailored components

**Don't: Ignore Mobile**
- v0.dev generates responsive code
- But you must specify the behavior

---

## Resources

- [v0.dev](https://v0.dev) - Vercel's AI UI generation
- [shadcn/ui](https://ui.shadcn.com/) - Component library
- [Tailwind CSS](https://tailwindcss.com/) - Utility CSS
- [Lucide Icons](https://lucide.dev/) - Icon library

---

**Version**: 1.0
**Last Updated**: 2025-12-14
**Source**: ADR-047, Sprint 50/51
