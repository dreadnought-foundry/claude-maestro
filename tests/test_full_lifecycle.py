#!/usr/bin/env python3
"""
Full Epic/Sprint Lifecycle End-to-End Test.

This test runs through the COMPLETE lifecycle:
1. Create epic
2. Create sprints in epic
3. Start epic
4. Start each sprint
5. Complete each sprint
6. Complete epic
7. Archive epic
8. Verify final state

Can be run as:
    python tests/test_full_lifecycle.py          # Standalone
    pytest tests/test_full_lifecycle.py -v       # With pytest
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sprint_lifecycle import (
    # Epic operations
    create_epic,
    start_epic,
    complete_epic,
    archive_epic,
    # Sprint operations
    create_sprint,
    start_sprint,
    complete_sprint,
)


class FullLifecycleTest:
    """Full end-to-end lifecycle test."""

    def __init__(self):
        self.temp_dir = None
        self.project_root = None
        self.results = []

    def setup(self):
        """Create temporary project structure."""
        self.temp_dir = tempfile.mkdtemp(prefix="lifecycle_test_")
        self.project_root = Path(self.temp_dir)

        # Create full project structure
        dirs = [
            ".claude",
            "docs/sprints/0-backlog",
            "docs/sprints/1-todo",
            "docs/sprints/2-in-progress",
            "docs/sprints/3-done/_standalone",
            "docs/sprints/4-blocked",
            "docs/sprints/5-aborted",
            "docs/sprints/6-archived",
            "scripts",
        ]
        for d in dirs:
            (self.project_root / d).mkdir(parents=True, exist_ok=True)

        # Create registry
        registry = {
            "version": "1.0",
            "counters": {"next_sprint": 1, "next_epic": 1},
            "sprints": {},
            "epics": {},
        }
        registry_path = self.project_root / "docs" / "sprints" / "registry.json"
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        # Create sprint steps file (required for start_sprint)
        steps_file = self.project_root / ".claude" / "sprint-steps.json"
        steps_data = {
            "version": "3.1",
            "step_order": ["1.1", "1.2", "2.1", "2.2", "3.1", "4.1", "5.1"],
            "phases": [
                {
                    "phase": 1,
                    "name": "Planning",
                    "steps": [
                        {"step": "1.1", "name": "Read Sprint"},
                        {"step": "1.2", "name": "Design"},
                    ],
                },
                {
                    "phase": 2,
                    "name": "Implementation",
                    "steps": [
                        {"step": "2.1", "name": "Write Tests"},
                        {"step": "2.2", "name": "Implement"},
                    ],
                },
                {
                    "phase": 3,
                    "name": "Review",
                    "steps": [{"step": "3.1", "name": "Quality Review"}],
                },
                {
                    "phase": 4,
                    "name": "Documentation",
                    "steps": [{"step": "4.1", "name": "Document"}],
                },
                {
                    "phase": 5,
                    "name": "Commit",
                    "steps": [{"step": "5.1", "name": "Commit Changes"}],
                },
            ],
        }
        with open(steps_file, "w") as f:
            json.dump(steps_data, f, indent=2)

        print(f"Created test project at: {self.project_root}")

    def teardown(self):
        """Clean up temporary directory."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up: {self.temp_dir}")

    def log(self, step: str, status: str, details: str = ""):
        """Log a test step result."""
        icon = "✓" if status == "PASS" else "✗"
        self.results.append((step, status, details))
        print(f"  {icon} {step}: {details}" if details else f"  {icon} {step}")

    def verify_path_exists(self, path: Path, description: str) -> bool:
        """Verify a path exists."""
        if path.exists():
            self.log(description, "PASS", str(path.name))
            return True
        else:
            self.log(description, "FAIL", f"Not found: {path}")
            return False

    def verify_path_not_exists(self, path: Path, description: str) -> bool:
        """Verify a path does NOT exist (was moved)."""
        if not path.exists():
            self.log(description, "PASS", "correctly moved")
            return True
        else:
            self.log(description, "FAIL", f"Still exists: {path}")
            return False

    def run_full_lifecycle(self):
        """Run the complete epic/sprint lifecycle."""
        print("\n" + "=" * 60)
        print("FULL EPIC/SPRINT LIFECYCLE TEST")
        print("=" * 60)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=self.project_root
        ):
            with patch("subprocess.run") as mock_run:
                with patch(
                    "scripts.sprint_lifecycle.check_git_clean", return_value=True
                ):
                    mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

                    # ========================================
                    # PHASE 1: CREATE EPIC
                    # ========================================
                    print("\n--- Phase 1: Create Epic ---")
                    try:
                        result = create_epic(1, "Test Epic", dry_run=False)
                        self.log("Create epic 1", "PASS", result.get("title", ""))

                        epic_path = (
                            self.project_root / "docs/sprints/1-todo/epic-01_test-epic"
                        )
                        self.verify_path_exists(epic_path, "Epic folder in 1-todo")
                        self.verify_path_exists(
                            epic_path / "_epic.md", "Epic file exists"
                        )
                    except Exception as e:
                        self.log("Create epic 1", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 2: CREATE SPRINTS IN EPIC
                    # ========================================
                    print("\n--- Phase 2: Create Sprints in Epic ---")
                    try:
                        result1 = create_sprint(
                            1, "First Sprint", epic=1, dry_run=False
                        )
                        self.log(
                            "Create sprint 1 in epic", "PASS", result1.get("title", "")
                        )

                        result2 = create_sprint(
                            2, "Second Sprint", epic=1, dry_run=False
                        )
                        self.log(
                            "Create sprint 2 in epic", "PASS", result2.get("title", "")
                        )

                        # Verify sprints are in epic folder (as subdirectories)
                        sprint1_path = (
                            epic_path
                            / "sprint-01_first-sprint"
                            / "sprint-01_first-sprint.md"
                        )
                        sprint2_path = (
                            epic_path
                            / "sprint-02_second-sprint"
                            / "sprint-02_second-sprint.md"
                        )
                        self.verify_path_exists(sprint1_path, "Sprint 1 in epic folder")
                        self.verify_path_exists(sprint2_path, "Sprint 2 in epic folder")
                    except Exception as e:
                        self.log("Create sprints", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 3: START EPIC
                    # ========================================
                    print("\n--- Phase 3: Start Epic ---")
                    try:
                        result = start_epic(1, dry_run=False)
                        self.log("Start epic 1", "PASS")

                        # Verify epic moved to in-progress
                        old_path = (
                            self.project_root / "docs/sprints/1-todo/epic-01_test-epic"
                        )
                        new_path = (
                            self.project_root
                            / "docs/sprints/2-in-progress/epic-01_test-epic"
                        )
                        self.verify_path_not_exists(old_path, "Epic not in 1-todo")
                        self.verify_path_exists(new_path, "Epic in 2-in-progress")
                    except Exception as e:
                        self.log("Start epic 1", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 4: START AND COMPLETE SPRINT 1
                    # ========================================
                    print("\n--- Phase 4: Start & Complete Sprint 1 ---")
                    try:
                        # Start sprint 1
                        result = start_sprint(1, dry_run=False)
                        self.log("Start sprint 1", "PASS")

                        # Verify state file created
                        state_file = self.project_root / ".claude/sprint-1-state.json"
                        self.verify_path_exists(state_file, "Sprint 1 state file")

                        # Add postmortem section to sprint file (required for completion)
                        epic_in_progress = (
                            self.project_root
                            / "docs/sprints/2-in-progress/epic-01_test-epic"
                        )
                        sprint1_file = (
                            epic_in_progress
                            / "sprint-01_first-sprint"
                            / "sprint-01_first-sprint.md"
                        )
                        if sprint1_file.exists():
                            content = sprint1_file.read_text()
                            if "## Postmortem" not in content:
                                content += (
                                    "\n\n## Postmortem\n\nCompleted successfully.\n"
                                )
                                sprint1_file.write_text(content)

                        # Complete sprint 1
                        result = complete_sprint(1, dry_run=False)
                        self.log("Complete sprint 1", "PASS")

                        # Verify sprint folder renamed with --done
                        done_sprint1 = (
                            epic_in_progress
                            / "sprint-01_first-sprint--done"
                            / "sprint-01_first-sprint--done.md"
                        )
                        self.verify_path_exists(done_sprint1, "Sprint 1 marked done")
                    except Exception as e:
                        self.log("Sprint 1 lifecycle", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 5: START AND COMPLETE SPRINT 2
                    # ========================================
                    print("\n--- Phase 5: Start & Complete Sprint 2 ---")
                    try:
                        # Start sprint 2
                        result = start_sprint(2, dry_run=False)
                        self.log("Start sprint 2", "PASS")

                        # Verify state file created
                        state_file = self.project_root / ".claude/sprint-2-state.json"
                        self.verify_path_exists(state_file, "Sprint 2 state file")

                        # Add postmortem section
                        sprint2_file = (
                            epic_in_progress
                            / "sprint-02_second-sprint"
                            / "sprint-02_second-sprint.md"
                        )
                        if sprint2_file.exists():
                            content = sprint2_file.read_text()
                            if "## Postmortem" not in content:
                                content += (
                                    "\n\n## Postmortem\n\nCompleted successfully.\n"
                                )
                                sprint2_file.write_text(content)

                        # Complete sprint 2
                        result = complete_sprint(2, dry_run=False)
                        self.log("Complete sprint 2", "PASS")

                        # Verify sprint folder renamed with --done
                        done_sprint2 = (
                            epic_in_progress
                            / "sprint-02_second-sprint--done"
                            / "sprint-02_second-sprint--done.md"
                        )
                        self.verify_path_exists(done_sprint2, "Sprint 2 marked done")
                    except Exception as e:
                        self.log("Sprint 2 lifecycle", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 6: COMPLETE EPIC
                    # ========================================
                    print("\n--- Phase 6: Complete Epic ---")
                    try:
                        result = complete_epic(1, dry_run=False)
                        self.log("Complete epic 1", "PASS")

                        # Verify epic moved to done
                        old_path = (
                            self.project_root
                            / "docs/sprints/2-in-progress/epic-01_test-epic"
                        )
                        new_path = (
                            self.project_root / "docs/sprints/3-done/epic-01_test-epic"
                        )
                        self.verify_path_not_exists(
                            old_path, "Epic not in 2-in-progress"
                        )
                        self.verify_path_exists(new_path, "Epic in 3-done")
                    except Exception as e:
                        self.log("Complete epic 1", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 7: ARCHIVE EPIC
                    # ========================================
                    print("\n--- Phase 7: Archive Epic ---")
                    try:
                        result = archive_epic(1, dry_run=False)
                        self.log("Archive epic 1", "PASS")

                        # Verify epic moved to archived
                        old_path = (
                            self.project_root / "docs/sprints/3-done/epic-01_test-epic"
                        )
                        new_path = (
                            self.project_root
                            / "docs/sprints/6-archived/epic-01_test-epic"
                        )
                        self.verify_path_not_exists(old_path, "Epic not in 3-done")
                        self.verify_path_exists(new_path, "Epic in 6-archived")

                        # Verify sprints are still in archived epic (in folders)
                        self.verify_path_exists(
                            new_path
                            / "sprint-01_first-sprint--done"
                            / "sprint-01_first-sprint--done.md",
                            "Sprint 1 in archived epic",
                        )
                        self.verify_path_exists(
                            new_path
                            / "sprint-02_second-sprint--done"
                            / "sprint-02_second-sprint--done.md",
                            "Sprint 2 in archived epic",
                        )
                    except Exception as e:
                        self.log("Archive epic 1", "FAIL", str(e))
                        return False

                    # ========================================
                    # PHASE 8: VERIFY FINAL STATE
                    # ========================================
                    print("\n--- Phase 8: Verify Final State ---")

                    # Check registry
                    registry_path = self.project_root / "docs/sprints/registry.json"
                    with open(registry_path) as f:
                        registry = json.load(f)

                    if "1" in registry.get("sprints", {}):
                        self.log("Sprint 1 in registry", "PASS")
                    else:
                        self.log("Sprint 1 in registry", "FAIL")

                    if "2" in registry.get("sprints", {}):
                        self.log("Sprint 2 in registry", "PASS")
                    else:
                        self.log("Sprint 2 in registry", "FAIL")

                    return True

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, status, _ in self.results if status == "PASS")
        failed = sum(1 for _, status, _ in self.results if status == "FAIL")

        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print("=" * 60)

        if failed == 0:
            print("✓ ALL TESTS PASSED - Full lifecycle works correctly!")
            return True
        else:
            print("✗ SOME TESTS FAILED")
            print("\nFailed steps:")
            for step, status, details in self.results:
                if status == "FAIL":
                    print(f"  - {step}: {details}")
            return False


def run_test():
    """Run the full lifecycle test."""
    test = FullLifecycleTest()
    try:
        test.setup()
        test.run_full_lifecycle()
        return test.print_summary()
    finally:
        test.teardown()


# Pytest compatible test
def test_full_epic_sprint_lifecycle():
    """Pytest wrapper for full lifecycle test."""
    assert run_test() is True


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
