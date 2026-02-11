---
description: "Abandon an epic and all its sprints"
allowed-tools: [Bash, Read, Glob, AskUserQuestion]
---

# Abandon Epic

Abandon Epic $ARGUMENTS and all its sprints.

## Instructions

### 1. Find the Epic

Search for the epic folder in todo, in-progress, or blocked:

```bash
# Look in 1-todo, 2-in-progress, or 4-blocked
find docs/sprints -type d -name "epic-$ARGUMENTS_*" 2>/dev/null | head -1
```

If not found, inform the user and stop.

### 2. Read Epic Details

Read the `_epic.md` file to get the title and list of sprints.

### 3. List All Sprints in Epic

Find all sprint files in the epic folder:

```bash
find <epic_folder> -name "sprint-*.md" -type f
```

### 4. Confirm with User

Use AskUserQuestion to confirm:

**Question**: "Are you sure you want to abandon Epic $ARGUMENTS: {title}?"

**Options**:
- "Yes, abandon this epic" - Proceed with abandonment
- "No, keep it" - Cancel and stop

**Include in the question**: List all sprints that will be aborted.

### 5. If Confirmed, Execute Abandonment

#### 5a. Move Epic Folder to 5-abandoned

```bash
mkdir -p docs/sprints/5-abandoned
mv <epic_folder> docs/sprints/5-abandoned/
```

#### 5b. Update Epic YAML Frontmatter

Edit the `_epic.md` file to update:
- `status: abandoned`
- `abandoned_at: <current timestamp>`

#### 5c. Abort Each Sprint

For each sprint file found, extract the sprint number and run:

```bash
/sprint-abort <sprint_number>
```

Use the Skill tool to invoke sprint-abort for each sprint.

### 6. Report Results

Output:
```
Epic $ARGUMENTS: {title} - ABANDONED

Location: docs/sprints/5-abandoned/{epic_folder_name}

Sprints aborted:
- Sprint {N1}: {title1}
- Sprint {N2}: {title2}
...

The epic and all its sprints have been moved to abandoned status.
```
