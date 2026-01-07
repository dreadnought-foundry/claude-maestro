"""
Project creation and initialization.

Handles creation of new Claude Code projects with sprint workflow system.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from ..exceptions import FileOperationError, ValidationError


def create_project(target_path: Optional[str] = None, dry_run: bool = False) -> dict:
    """
    Initialize a new project with the complete sprint workflow system.

    Supports dual-mode operation:
    - Maestro mode: If templates/project/ exists in target, copy FROM local templates
    - Normal mode: Copy FROM ~/.claude/templates/project/ (standard projects)

    Args:
        target_path: Target directory path (defaults to current directory)
        dry_run: If True, preview changes without executing

    Returns:
        Dict with initialization summary including 'maestro_mode' flag

    Raises:
        FileOperationError: If target doesn't exist or master template not found
        ValidationError: If project already initialized

    Example:
        >>> summary = create_project("/path/to/new/project")
        >>> print(summary['status'])  # 'initialized'
    """

    # 1. Determine target path
    if target_path:
        target = Path(target_path).resolve()
    else:
        target = Path.cwd().resolve()

    # 2. Validate target
    if not target.exists():
        raise FileOperationError(f"Directory not found: {target}")

    # Check if already initialized
    if (target / ".claude" / "sprint-steps.json").exists():
        raise ValidationError(
            f"Project already initialized at {target}\n"
            f"Use /project-update to sync changes instead."
        )

    # 3. Detect maestro mode
    maestro_mode = (target / "templates" / "project").exists()

    # 4. Define source paths based on mode
    master_project = Path.home() / "Development" / "Dreadnought" / "claude-maestro"
    global_claude = Path.home() / ".claude"

    if maestro_mode:
        # Maestro mode: Use local templates
        template_path = target / "templates" / "project"
        print("🔧 MAESTRO MODE: Initializing from local templates")
        print(f"   Source: {template_path}")
    else:
        # Normal mode: Use global templates
        template_path = global_claude / "templates" / "project"
        # Validate master project exists for normal mode
        if not master_project.exists():
            raise FileOperationError(
                f"Master project not found at {master_project}\n"
                f"Cannot initialize without template source."
            )

    if dry_run:
        print(f"[DRY RUN] Would initialize project at: {target}")
        print("\nWould create structure:")
        print(f"  ├── commands/ (from {master_project}/commands/)")
        print(f"  ├── scripts/ (from {master_project}/scripts/)")
        print("  ├── .claude/")
        print("  │   ├── agents/ (global + template)")
        print("  │   ├── hooks/ (global + template)")
        print("  │   ├── settings.json")
        print("  │   ├── sprint-steps.json")
        print("  │   └── WORKFLOW_VERSION")
        print("  ├── docs/sprints/")
        print("  │   ├── 0-backlog/")
        print("  │   ├── 1-todo/")
        print("  │   ├── 2-in-progress/")
        print("  │   ├── 3-done/")
        print("  │   ├── 4-blocked/")
        print("  │   ├── 5-aborted/")
        print("  │   ├── 6-archived/")
        print("  │   └── registry.json")
        print("  ├── CLAUDE.md")
        print("  └── .gitignore (updated)")
        return {"status": "dry-run", "target": str(target)}

    # 5. Create directory structure
    print("→ Creating directory structure...")
    dirs_to_create = [
        target / ".claude" / "agents",
        target / ".claude" / "hooks",
        target / "docs" / "sprints" / "0-backlog",
        target / "docs" / "sprints" / "1-todo",
        target / "docs" / "sprints" / "2-in-progress",
        target / "docs" / "sprints" / "3-done",
        target / "docs" / "sprints" / "4-blocked",
        target / "docs" / "sprints" / "5-aborted",
        target / "docs" / "sprints" / "6-archived",
    ]

    # Only create commands/ and scripts/ for normal projects
    if not maestro_mode:
        dirs_to_create.extend(
            [
                target / "commands",
                target / "scripts",
            ]
        )

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    print("✓ Created directory structure")

    # 6. Copy commands from master project (skip in maestro mode)
    command_count = 0
    if not maestro_mode:
        print("→ Copying commands...")
        if (master_project / "commands").exists():
            for cmd_file in (master_project / "commands").glob("*.md"):
                shutil.copy2(cmd_file, target / "commands" / cmd_file.name)
                command_count += 1
        print(f"✓ Copied {command_count} command files")
    else:
        print("✓ Skipping commands/ (maestro mode - already exists)")

    # 7. Copy scripts from master project (skip in maestro mode)
    if not maestro_mode:
        print("→ Copying scripts...")
        if (master_project / "scripts").exists():
            for script_file in (master_project / "scripts").iterdir():
                if script_file.is_file():
                    dest = target / "scripts" / script_file.name
                    shutil.copy2(script_file, dest)
                    # Make Python scripts executable
                    if script_file.suffix == ".py":
                        dest.chmod(0o755)
        print("✓ Copied automation scripts")
    else:
        print("✓ Skipping scripts/ (maestro mode - already exists)")

    # 7. Copy agents (global + template)
    print("→ Copying agents...")
    agent_count = 0

    # Copy global agents
    if (global_claude / "agents").exists():
        for agent_file in (global_claude / "agents").glob("*.md"):
            shutil.copy2(agent_file, target / ".claude" / "agents" / agent_file.name)
            agent_count += 1

    # Copy template agents
    if (template_path / ".claude" / "agents").exists():
        for agent_file in (template_path / ".claude" / "agents").glob("*.md"):
            shutil.copy2(agent_file, target / ".claude" / "agents" / agent_file.name)
            agent_count += 1

    print(f"✓ Copied {agent_count} agents")

    # 8. Copy hooks (global + template)
    print("→ Copying hooks...")
    hook_count = 0

    # Copy global hooks
    if (global_claude / "hooks").exists():
        for hook_file in (global_claude / "hooks").glob("*.py"):
            dest = target / ".claude" / "hooks" / hook_file.name
            shutil.copy2(hook_file, dest)
            dest.chmod(0o755)
            hook_count += 1

    # Copy template hooks
    if (template_path / ".claude" / "hooks").exists():
        for hook_file in (template_path / ".claude" / "hooks").glob("*.py"):
            dest = target / ".claude" / "hooks" / hook_file.name
            shutil.copy2(hook_file, dest)
            dest.chmod(0o755)
            hook_count += 1

    print(f"✓ Copied {hook_count} hooks")

    # 9. Copy configuration files
    print("→ Copying configuration...")

    # Copy sprint-steps.json
    if (template_path / ".claude" / "sprint-steps.json").exists():
        shutil.copy2(
            template_path / ".claude" / "sprint-steps.json",
            target / ".claude" / "sprint-steps.json",
        )

    # Copy settings.json
    if (template_path / ".claude" / "settings.json").exists():
        shutil.copy2(
            template_path / ".claude" / "settings.json",
            target / ".claude" / "settings.json",
        )

    # Copy WORKFLOW_VERSION
    if (master_project / "WORKFLOW_VERSION").exists():
        shutil.copy2(
            master_project / "WORKFLOW_VERSION", target / ".claude" / "WORKFLOW_VERSION"
        )

    print("✓ Copied configuration files")

    # 10. Copy CLAUDE.md (don't overwrite if exists)
    print("→ Copying CLAUDE.md...")
    if not (target / "CLAUDE.md").exists():
        if (template_path / "CLAUDE.md").exists():
            shutil.copy2(template_path / "CLAUDE.md", target / "CLAUDE.md")
            print("✓ Created CLAUDE.md")
        else:
            print("⚠ Template CLAUDE.md not found, skipping")
    else:
        print("✓ CLAUDE.md already exists, skipping")

    # 11. Create sprint registry
    print("→ Creating sprint registry...")
    registry = {
        "counters": {"next_sprint": 1, "next_epic": 1},
        "sprints": {},
        "epics": {},
    }

    registry_path = target / "docs" / "sprints" / "registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)

    print("✓ Created sprint registry")

    # 12. Update .gitignore
    print("→ Updating .gitignore...")
    gitignore_path = target / ".gitignore"
    gitignore_entries = [
        "# Sprint workflow state files",
        ".claude/sprint-*-state.json",
        ".claude/product-state.json",
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "sprint-.*-state.json" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n")
                f.write("\n".join(gitignore_entries))
                f.write("\n")
            print("✓ Updated .gitignore")
        else:
            print("✓ .gitignore already configured")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(gitignore_entries))
            f.write("\n")
        print("✓ Created .gitignore")

    # Read workflow version
    workflow_version = "unknown"
    if (target / ".claude" / "WORKFLOW_VERSION").exists():
        workflow_version = (target / ".claude" / "WORKFLOW_VERSION").read_text().strip()

    # 13. Report success
    print(f"\n{'='*70}")
    if maestro_mode:
        print(f"✅ Maestro workflow initialized at: {target}")
        print(f"{'='*70}")
        print("\n🔧 MAESTRO MODE - Dogfooding the workflow")
        print("   Source: ./templates/project/")
    else:
        print(f"✅ Project workflow initialized at: {target}")
        print(f"{'='*70}")

    print("\nCreated structure:")
    if not maestro_mode:
        print(f"├── commands/             ({command_count} command files)")
        print("├── scripts/              (automation)")
    print("├── .claude/")
    print(f"│   ├── agents/           ({agent_count} agents)")
    print(f"│   ├── hooks/            ({hook_count} hooks)")
    print("│   ├── settings.json")
    print("│   ├── sprint-steps.json")
    print("│   └── WORKFLOW_VERSION")
    print("├── docs/sprints/")
    print("│   ├── 0-backlog/")
    print("│   ├── 1-todo/")
    print("│   ├── 2-in-progress/")
    print("│   ├── 3-done/")
    print("│   ├── 4-blocked/")
    print("│   ├── 5-aborted/")
    print("│   ├── 6-archived/")
    print("│   └── registry.json")
    print("└── CLAUDE.md")

    print("\nNext steps:")
    if maestro_mode:
        print("1. Use sprints to develop maestro itself (dogfooding)")
        print('2. Create sprint: /sprint-new "Feature Name"')
        print("3. Start working: /sprint-start N")
        print("4. Publish templates: /maestro-publish (when ready)")
    else:
        print("1. Review and customize CLAUDE.md for your project")
        print('2. Create your first sprint: /sprint-new "Initial Setup"')
        print("3. Start working: /sprint-start 1")

    print("\nTo sync future updates: /project-update")
    print(f"Workflow version: {workflow_version}")
    print(f"{'='*70}")

    return {
        "status": "initialized",
        "target": str(target),
        "maestro_mode": maestro_mode,
        "command_count": command_count,
        "agent_count": agent_count,
        "hook_count": hook_count,
        "workflow_version": workflow_version,
    }
