"""Tests for sprint automation functions (Batches 1-4 + project-create).

These tests validate the high-level automation functions that orchestrate
multiple operations for sprint/epic lifecycle management.

Test Coverage:
- Batch 1: Core lifecycle (start_sprint, complete_sprint, abort_sprint)
- Batch 2: Epic lifecycle (start_epic, complete_epic, archive_epic)
- Batch 3: State management (block_sprint, resume_sprint, advance_step, generate_postmortem)
- Batch 4: Queries & utilities (get_sprint_status, get_epic_status, list_epics, recover_sprint, add_to_epic)
- Project Setup: create_project
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from sprint_lifecycle.py
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sprint_lifecycle import (
    # Batch 1: Core lifecycle
    start_sprint,
    complete_sprint,
    abort_sprint,
    # Batch 2: Epic lifecycle
    start_epic,
    complete_epic,
    archive_epic,
    # Batch 3: State management
    block_sprint,
    resume_sprint,
    advance_step,
    generate_postmortem,
    # Batch 4: Queries & utilities
    get_sprint_status,
    get_epic_status,
    list_epics,
    recover_sprint,
    add_to_epic,
    # Project setup
    create_project,
    # Utilities
    FileOperationError,
    ValidationError,
)


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create project structure
        (project_root / ".claude").mkdir()
        (project_root / "docs" / "sprints" / "0-backlog").mkdir(parents=True)
        (project_root / "docs" / "sprints" / "1-todo").mkdir(parents=True)
        (project_root / "docs" / "sprints" / "2-in-progress").mkdir(parents=True)
        (project_root / "docs" / "sprints" / "3-done" / "_standalone").mkdir(
            parents=True
        )
        (project_root / "docs" / "sprints" / "4-blocked").mkdir(parents=True)
        (project_root / "docs" / "sprints" / "5-aborted").mkdir(parents=True)
        (project_root / "docs" / "sprints" / "6-archived").mkdir(parents=True)
        (project_root / "scripts").mkdir()

        # Create registry
        registry = {
            "counters": {"next_sprint": 1, "next_epic": 1},
            "sprints": {},
            "epics": {},
        }
        registry_path = project_root / "docs" / "sprints" / "registry.json"
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        yield project_root


@pytest.fixture
def sprint_in_todo(temp_project):
    """Create a sprint file in 1-todo."""
    sprint_path = (
        temp_project / "docs" / "sprints" / "1-todo" / "sprint-05_test-sprint.md"
    )
    content = """---
sprint: 5
title: Test Sprint
status: todo
workflow_version: "3.1.0"
epic: null
created: 2025-12-30
started: null
completed: null
hours: null
---

# Sprint 5: Test Sprint

## Overview
Test sprint for automation.
"""
    sprint_path.write_text(content)
    return sprint_path


@pytest.fixture
def sprint_in_progress(temp_project):
    """Create a sprint file in 2-in-progress with state file."""
    sprint_path = (
        temp_project
        / "docs"
        / "sprints"
        / "2-in-progress"
        / "sprint-10_active-sprint.md"
    )
    content = """---
sprint: 10
title: Active Sprint
status: in-progress
workflow_version: "3.1.0"
epic: null
created: 2025-12-30
started: 2025-12-30T10:00:00Z
completed: null
hours: null
---

# Sprint 10: Active Sprint

## Overview
Active sprint.

## Postmortem
Metrics and learnings.
"""
    sprint_path.write_text(content)

    # Create state file
    state = {
        "sprint_number": 10,
        "sprint_file": str(sprint_path),
        "sprint_title": "Active Sprint",
        "status": "in_progress",
        "workflow_version": "3.1.0",
        "started_at": "2025-12-30T10:00:00Z",
        "current_step": "2.1",
    }
    state_path = temp_project / ".claude" / "sprint-10-state.json"
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    return sprint_path


@pytest.fixture
def epic_in_progress(temp_project):
    """Create an epic folder with sprints."""
    epic_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-03_test-epic"
    epic_dir.mkdir()

    # Create _epic.md
    epic_content = """---
epic: 3
title: Test Epic
status: in-progress
created: 2025-12-30
sprint_count: 3
---

# Epic 03: Test Epic

## Overview
Test epic with multiple sprints.
"""
    (epic_dir / "_epic.md").write_text(epic_content)

    # Create sprints
    (epic_dir / "sprint-01_first--done.md").write_text(
        "---\nsprint: 1\ntitle: First\n---\n# Sprint 1"
    )
    (epic_dir / "sprint-02_second.md").write_text(
        "---\nsprint: 2\ntitle: Second\n---\n# Sprint 2"
    )
    (epic_dir / "sprint-03_third.md").write_text(
        "---\nsprint: 3\ntitle: Third\n---\n# Sprint 3"
    )

    return epic_dir


# ============================================================================
# BATCH 1: CORE LIFECYCLE TESTS
# ============================================================================


class TestStartSprint:
    """Test start_sprint() function."""

    def test_start_sprint_moves_file_and_creates_state(
        self, temp_project, sprint_in_todo
    ):
        """Should move sprint from todo to in-progress and create state file."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = start_sprint(5)

        # Verify file moved
        assert not sprint_in_todo.exists()
        new_path = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "sprint-05_test-sprint.md"
        )
        assert new_path.exists()

        # Verify state file created
        state_path = temp_project / ".claude" / "sprint-5-state.json"
        assert state_path.exists()

        with open(state_path) as f:
            state = json.load(f)

        assert state["sprint_number"] == 5
        assert state["status"] == "in_progress"
        assert "started_at" in state

        # Verify result
        assert result["sprint_num"] == 5
        assert result["title"] == "Test Sprint"
        assert "file_path" in result  # Returns file_path not new_path

    def test_start_sprint_dry_run(self, temp_project, sprint_in_todo, capsys):
        """Should preview changes without executing in dry-run mode."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = start_sprint(5, dry_run=True)

        # File should not have moved
        assert sprint_in_todo.exists()

        # State file should not exist
        state_path = temp_project / ".claude" / "sprint-5-state.json"
        assert not state_path.exists()

        # Should print dry-run output
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert result["status"] == "dry-run"

    def test_start_sprint_not_found(self, temp_project):
        """Should raise error when sprint doesn't exist."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="Sprint 999 not found"):
                start_sprint(999)


class TestCompleteSprint:
    """Test complete_sprint() function."""

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_complete_sprint_full_workflow(
        self, mock_run, mock_clean, temp_project, sprint_in_progress
    ):
        """Should execute full completion workflow."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            complete_sprint(10)

        # Verify file moved with --done suffix
        new_path = (
            temp_project
            / "docs"
            / "sprints"
            / "3-done"
            / "_standalone"
            / "sprint-10_active-sprint--done.md"
        )
        assert new_path.exists()
        assert not sprint_in_progress.exists()

        # Verify registry updated
        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        with open(registry_path) as f:
            registry = json.load(f)

        assert "10" in registry["sprints"]
        assert registry["sprints"]["10"]["status"] == "done"
        assert "hours" in registry["sprints"]["10"]

        # Verify git commands called (add, commit, tag, push)
        assert mock_run.call_count >= 2  # At minimum: git add, git commit

    def test_complete_sprint_missing_postmortem(self, temp_project):
        """Should raise error when postmortem missing."""
        # Create sprint without postmortem
        sprint_path = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "sprint-99_no-postmortem.md"
        )
        content = """---
sprint: 99
title: No Postmortem
status: in-progress
started: 2025-12-30T10:00:00Z
---

# Sprint 99
"""
        sprint_path.write_text(content)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(ValidationError, match="missing postmortem"):
                complete_sprint(99)

    def test_complete_sprint_dry_run(self, temp_project, sprint_in_progress, capsys):
        """Should preview completion without executing."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            complete_sprint(10, dry_run=True)

        # File should not have moved
        assert sprint_in_progress.exists()

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Would complete sprint 10" in captured.out


class TestAbortSprint:
    """Test abort_sprint() function."""

    def test_abort_sprint_renames_with_aborted_suffix(
        self, temp_project, sprint_in_progress
    ):
        """Should rename sprint with --aborted suffix and update state."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = abort_sprint(10, "Requirements changed")

        # Verify file renamed (stays in same folder, just adds --aborted suffix)
        assert not sprint_in_progress.exists()
        new_path = sprint_in_progress.parent / "sprint-10_active-sprint--aborted.md"
        assert new_path.exists()

        # Verify YAML updated
        content = new_path.read_text()
        assert "status: aborted" in content

        # Verify state file updated
        state_path = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_path) as f:
            state = json.load(f)

        assert state["status"] == "aborted"
        assert "aborted_at" in state

        # Verify result
        assert result["sprint_num"] == 10
        assert "hours" in result

    def test_abort_sprint_dry_run(self, temp_project, sprint_in_progress, capsys):
        """Should preview abort without executing."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            abort_sprint(10, "Test", dry_run=True)

        assert sprint_in_progress.exists()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out


# ============================================================================
# BATCH 2: EPIC LIFECYCLE TESTS
# ============================================================================


class TestStartEpic:
    """Test start_epic() function."""

    def test_start_epic_moves_to_in_progress(self, temp_project):
        """Should move epic folder from todo to in-progress."""
        # Create epic in todo
        epic_dir = temp_project / "docs" / "sprints" / "1-todo" / "epic-05_new-epic"
        epic_dir.mkdir()
        (epic_dir / "_epic.md").write_text(
            "---\nepic: 5\ntitle: New Epic\n---\n# Epic 5"
        )
        (epic_dir / "sprint-01_test.md").write_text("# Sprint 1")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = start_epic(5)

        # Verify folder moved
        assert not epic_dir.exists()
        new_path = (
            temp_project / "docs" / "sprints" / "2-in-progress" / "epic-05_new-epic"
        )
        assert new_path.exists()
        assert (new_path / "_epic.md").exists()
        assert (new_path / "sprint-01_test.md").exists()

        # Verify result
        assert result["epic_num"] == 5
        assert result["title"] == "New Epic"
        assert result["sprint_count"] == 1

    def test_start_epic_dry_run(self, temp_project, capsys):
        """Should preview start without executing."""
        epic_dir = temp_project / "docs" / "sprints" / "1-todo" / "epic-06_test"
        epic_dir.mkdir()
        (epic_dir / "_epic.md").write_text("---\nepic: 6\ntitle: Test\n---\n# Epic")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            start_epic(6, dry_run=True)

        assert epic_dir.exists()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out


class TestCompleteEpic:
    """Test complete_epic() function."""

    def test_complete_epic_moves_to_done(self, temp_project, epic_in_progress):
        """Should move completed epic to 3-done."""
        # Mark all sprints as done
        for sprint_file in epic_in_progress.glob("sprint-*.md"):
            if not sprint_file.name.endswith("--done.md"):
                new_name = sprint_file.name.replace(".md", "--done.md")
                sprint_file.rename(sprint_file.parent / new_name)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = complete_epic(3)

        # Verify folder moved
        assert not epic_in_progress.exists()
        new_path = temp_project / "docs" / "sprints" / "3-done" / "epic-03_test-epic"
        assert new_path.exists()

        assert result["epic_num"] == 3
        assert result["done_count"] >= 1

    def test_complete_epic_with_active_sprints_fails(
        self, temp_project, epic_in_progress
    ):
        """Should raise error when active sprints remain."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(ValidationError, match="not complete"):
                complete_epic(3)


class TestArchiveEpic:
    """Test archive_epic() function."""

    def test_archive_epic_moves_to_archived(self, temp_project):
        """Should move epic from done to archived."""
        # Create epic in done
        epic_dir = temp_project / "docs" / "sprints" / "3-done" / "epic-10_old-epic"
        epic_dir.mkdir()
        (epic_dir / "_epic.md").write_text(
            "---\nepic: 10\ntitle: Old Epic\n---\n# Epic"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = archive_epic(10)

        # Verify moved to archived
        assert not epic_dir.exists()
        new_path = temp_project / "docs" / "sprints" / "6-archived" / "epic-10_old-epic"
        assert new_path.exists()

        assert result["epic_num"] == 10


# ============================================================================
# BATCH 3: STATE MANAGEMENT TESTS
# ============================================================================


class TestBlockSprint:
    """Test block_sprint() function."""

    def test_block_sprint_renames_with_blocked_suffix(
        self, temp_project, sprint_in_progress
    ):
        """Should rename sprint with --blocked suffix."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            block_sprint(10, "Waiting for API access")

        # Verify renamed (stays in same folder)
        new_path = sprint_in_progress.parent / "sprint-10_active-sprint--blocked.md"
        assert new_path.exists()
        assert not sprint_in_progress.exists()

        # Verify state updated
        state_path = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_path) as f:
            state = json.load(f)

        assert state["status"] == "blocked"
        assert state["blocker"] == "Waiting for API access"


class TestResumeSprint:
    """Test resume_sprint() function."""

    def test_resume_sprint_removes_blocked_suffix(self, temp_project):
        """Should remove --blocked suffix (stays in same folder)."""
        # Create blocked sprint in 2-in-progress
        blocked_path = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "sprint-15_blocked--blocked.md"
        )
        blocked_path.write_text(
            "---\nsprint: 15\ntitle: Blocked\nstatus: blocked\n---\n# Sprint"
        )

        # Create state
        state = {
            "sprint_number": 15,
            "status": "blocked",
            "blocker": "API access",
            "sprint_file": str(blocked_path),
        }
        state_path = temp_project / ".claude" / "sprint-15-state.json"
        with open(state_path, "w") as f:
            json.dump(state, f)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = resume_sprint(15)

        # Verify suffix removed (stays in same folder)
        assert not blocked_path.exists()
        new_path = blocked_path.parent / "sprint-15_blocked.md"
        assert new_path.exists()

        # Check result has expected fields
        assert result["sprint_num"] == 15
        assert "previous_blocker" in result  # May be "Unknown" if not in state


class TestAdvanceStep:
    """Test advance_step() function."""

    def test_advance_step_updates_state(self, temp_project, sprint_in_progress):
        """Should advance to next workflow step."""
        # Create sprint-steps.json in home directory mock
        steps_data = {
            "version": "3.1.0",
            "step_order": [
                "1.1",
                "1.2",
                "1.3",
                "1.4",
                "2.1",
                "2.2",
                "2.3",
                "2.4",
                "3.1",
                "3.2",
                "3.3",
                "3.4",
                "4.1",
            ],
            "phases": [
                {
                    "phase": 1,
                    "name": "Planning",
                    "steps": [
                        {"step": "1.1", "name": "Read Sprint"},
                        {"step": "1.2", "name": "Design Architecture"},
                        {"step": "1.3", "name": "Clarify Requirements"},
                        {"step": "1.4", "name": "Document Plan"},
                    ],
                },
                {
                    "phase": 2,
                    "name": "Test-First Implementation",
                    "steps": [
                        {"step": "2.1", "name": "Write Tests"},
                        {"step": "2.2", "name": "Implement Code"},
                        {"step": "2.3", "name": "Run Tests"},
                        {"step": "2.4", "name": "Fix Failures"},
                    ],
                },
                {
                    "phase": 3,
                    "name": "Validation & Refactoring",
                    "steps": [
                        {"step": "3.1", "name": "Verify Migrations"},
                        {"step": "3.2", "name": "Quality Review"},
                        {"step": "3.3", "name": "Refactor"},
                        {"step": "3.4", "name": "Re-test"},
                    ],
                },
                {
                    "phase": 4,
                    "name": "Documentation",
                    "steps": [{"step": "4.1", "name": "Generate Examples"}],
                },
            ],
        }

        # Mock Path.home() to return temp directory with sprint-steps.json
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project
            (temp_project / ".claude" / "sprint-steps.json").write_text(
                json.dumps(steps_data, indent=2)
            )

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                result = advance_step(10, dry_run=False)

        # Verify result
        assert result["sprint_num"] == 10
        assert result["previous_step"] == "2.1"
        assert result["new_step"] == "2.2"
        assert result["previous_step_name"] == "Write Tests"
        assert result["new_step_name"] == "Implement Code"

        # Verify state file updated
        state_path = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_path) as f:
            state = json.load(f)

        assert state["current_step"] == "2.2"
        assert state["current_phase"] == 2
        assert len(state.get("completed_steps", [])) == 1
        assert state["completed_steps"][0]["step"] == "2.1"

    def test_advance_step_dry_run(self, temp_project, sprint_in_progress):
        """Should preview step advancement without changing state."""
        # Create sprint-steps.json
        steps_data = {
            "version": "3.1.0",
            "step_order": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "2.3", "2.4"],
            "phases": [
                {
                    "phase": 2,
                    "name": "Test-First Implementation",
                    "steps": [
                        {"step": "2.1", "name": "Write Tests"},
                        {"step": "2.2", "name": "Implement Code"},
                    ],
                }
            ],
        }

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project
            (temp_project / ".claude" / "sprint-steps.json").write_text(
                json.dumps(steps_data, indent=2)
            )

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                result = advance_step(10, dry_run=True)

        # Verify result
        assert result["dry_run"] is True
        assert result["new_step"] == "2.2"

        # Verify state file NOT changed
        state_path = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_path) as f:
            state = json.load(f)

        assert state["current_step"] == "2.1"  # Still at original step
        assert (
            "completed_steps" not in state or len(state.get("completed_steps", [])) == 0
        )


class TestGeneratePostmortem:
    """Test generate_postmortem() function."""

    def test_generate_postmortem_creates_file(self, temp_project, sprint_in_progress):
        """Should create postmortem file and link from sprint."""
        # Add completed timestamp to state
        state_path = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_path) as f:
            state = json.load(f)
        state["completed_at"] = "2025-12-30T12:00:00Z"
        state["completed_steps"] = [
            {"step": "1.1", "completed_at": "2025-12-30T10:15:00Z"},
            {"step": "1.2", "completed_at": "2025-12-30T10:30:00Z"},
        ]
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = generate_postmortem(10, dry_run=False)

        # Verify result
        assert result["sprint_num"] == 10
        assert "postmortem_file" in result
        assert "metrics" in result

        # Verify postmortem file created
        postmortem_file = Path(result["postmortem_file"])
        assert postmortem_file.exists()
        content = postmortem_file.read_text()
        assert "Sprint 10 Postmortem" in content
        assert "Active Sprint" in content
        assert "## Metrics" in content
        assert "## What Went Well" in content
        assert "## What Could Improve" in content

        # Verify metrics calculated
        assert result["metrics"]["duration_hours"] == 2.0
        assert result["metrics"]["completed_steps"] == 2

        # Verify sprint file has link
        sprint_file = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "sprint-10_active-sprint.md"
        )
        sprint_content = sprint_file.read_text()
        assert "[Sprint 10 Postmortem](./sprint-10_postmortem.md)" in sprint_content

    def test_generate_postmortem_dry_run(self, temp_project, sprint_in_progress):
        """Should preview postmortem generation without creating files."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = generate_postmortem(10, dry_run=True)

        # Verify result
        assert result["dry_run"] is True
        assert result["sprint_num"] == 10

        # Verify postmortem file NOT created
        postmortem_file = Path(result["postmortem_file"])
        assert not postmortem_file.exists()


# ============================================================================
# BATCH 4: QUERIES & UTILITIES TESTS
# ============================================================================


class TestGetSprintStatus:
    """Test get_sprint_status() function."""

    def test_get_sprint_status_displays_info(
        self, temp_project, sprint_in_progress, capsys
    ):
        """Should display sprint status information."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            get_sprint_status(10)

        captured = capsys.readouterr()
        assert "Sprint 10" in captured.out
        assert "Active Sprint" in captured.out
        assert "in_progress" in captured.out or "in-progress" in captured.out


class TestGetEpicStatus:
    """Test get_epic_status() function."""

    def test_get_epic_status_displays_progress(
        self, temp_project, epic_in_progress, capsys
    ):
        """Should display epic status with sprint progress."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            get_epic_status(3)

        captured = capsys.readouterr()
        assert "Epic 3" in captured.out or "Epic 03" in captured.out
        assert "Test Epic" in captured.out


class TestListEpics:
    """Test list_epics() function."""

    def test_list_epics_shows_all_epics(self, temp_project, epic_in_progress, capsys):
        """Should list all epics with progress bars."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            list_epics()

        captured = capsys.readouterr()
        assert "Epic" in captured.out


class TestRecoverSprint:
    """Test recover_sprint() function."""

    def test_recover_sprint_standalone_in_wrong_location(self, temp_project):
        """Should move standalone sprint from wrong location to 3-done."""
        # Create a standalone sprint in wrong location (2-in-progress)
        wrong_dir = temp_project / "docs" / "sprints" / "2-in-progress"
        sprint_file = wrong_dir / "sprint-15_test-sprint--done.md"
        sprint_content = """---
sprint: 15
title: Test Sprint
status: done
---

# Sprint 15
"""
        sprint_file.write_text(sprint_content)

        # Create state file
        state_file = temp_project / ".claude" / "sprint-15-state.json"
        state = {"sprint_number": 15, "sprint_file": str(sprint_file), "status": "done"}
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Recover sprint
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = recover_sprint(15, dry_run=False)

        # Verify moved to correct location
        correct_path = (
            temp_project
            / "docs"
            / "sprints"
            / "3-done"
            / "sprint-15_test-sprint--done.md"
        )
        assert correct_path.exists()
        assert not sprint_file.exists()

        # Verify state file updated
        with open(state_file) as f:
            updated_state = json.load(f)
        assert updated_state["sprint_file"] == str(correct_path)

        # Verify result
        assert result["sprint_num"] == 15
        assert result["new_path"] == str(correct_path)

    def test_recover_sprint_dry_run(self, temp_project):
        """Should preview recovery without moving files."""
        # Create sprint in wrong location
        wrong_dir = temp_project / "docs" / "sprints" / "2-in-progress"
        sprint_file = wrong_dir / "sprint-20_another--done.md"
        sprint_file.write_text(
            "---\nsprint: 20\ntitle: Another\nstatus: done\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            result = recover_sprint(20, dry_run=True)

        # Verify no move happened
        assert sprint_file.exists()
        assert result["status"] == "dry-run"
        assert result["sprint_num"] == 20

    def test_recover_sprint_already_correct_location(self, temp_project):
        """Should raise error if sprint is already in correct location."""
        # Create sprint in correct location
        correct_dir = temp_project / "docs" / "sprints" / "3-done"
        sprint_file = correct_dir / "sprint-25_correct--done.md"
        sprint_file.write_text(
            "---\nsprint: 25\ntitle: Correct\nstatus: done\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(ValidationError, match="already in correct location"):
                recover_sprint(25, dry_run=False)

    def test_recover_sprint_not_done(self, temp_project):
        """Should raise error if sprint doesn't have --done suffix."""
        # Create sprint without --done suffix
        sprint_dir = temp_project / "docs" / "sprints" / "2-in-progress"
        sprint_file = sprint_dir / "sprint-30_not-done.md"
        sprint_file.write_text(
            "---\nsprint: 30\ntitle: Not Done\nstatus: in-progress\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(ValidationError, match="no --done suffix"):
                recover_sprint(30, dry_run=False)


class TestAddToEpic:
    """Test add_to_epic() function - already tested in test_sprint_lifecycle.py."""

    def test_add_to_epic_basic(self, temp_project, epic_in_progress):
        """Should add standalone sprint to epic."""
        # Create standalone sprint
        sprint_path = (
            temp_project / "docs" / "sprints" / "1-todo" / "sprint-50_standalone.md"
        )
        sprint_path.write_text(
            "---\nsprint: 50\ntitle: Standalone\nepic: null\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            add_to_epic(50, 3)

        # Verify moved into epic folder
        new_path = epic_in_progress / "sprint-50_standalone.md"
        assert new_path.exists()
        assert not sprint_path.exists()


# ============================================================================
# PROJECT SETUP TESTS
# ============================================================================


class TestCreateProject:
    """Test create_project() function."""

    def test_create_project_initializes_structure(self):
        """Should create complete project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            target.mkdir()

            # Mock the master project and templates
            with patch("scripts.sprint_lifecycle.Path.home") as mock_home:
                fake_home = Path(tmpdir) / "home"
                fake_home.mkdir()
                mock_home.return_value = fake_home

                # Create master project structure
                master = fake_home / "Development" / "Dreadnought" / "claude-maestro"
                master.mkdir(parents=True)
                (master / "commands").mkdir()
                (master / "scripts").mkdir()
                (master / "WORKFLOW_VERSION").write_text("3.1.0")

                # Create some command files
                (master / "commands" / "sprint-start.md").write_text("# Command")

                # Create templates
                template = fake_home / ".claude" / "templates" / "project"
                template.mkdir(parents=True)
                (template / ".claude" / "agents").mkdir(parents=True)
                (template / ".claude" / "hooks").mkdir(parents=True)
                (template / ".claude" / "sprint-steps.json").write_text("{}")
                (template / ".claude" / "settings.json").write_text("{}")
                (template / "CLAUDE.md").write_text("# Project")

                # Create global .claude
                (fake_home / ".claude" / "agents").mkdir(parents=True)
                (fake_home / ".claude" / "hooks").mkdir(parents=True)

                result = create_project(str(target))

                # Verify structure created
                assert (target / ".claude").exists()
                assert (target / "commands").exists()
                assert (target / "scripts").exists()
                assert (target / "docs" / "sprints" / "registry.json").exists()
                assert (target / "CLAUDE.md").exists()

                # Verify registry content
                with open(target / "docs" / "sprints" / "registry.json") as f:
                    registry = json.load(f)
                assert registry["counters"]["next_sprint"] == 1
                assert registry["counters"]["next_epic"] == 1

                assert result["status"] == "initialized"
                assert result["workflow_version"] == "3.1.0"

    def test_create_project_dry_run(self, capsys):
        """Should preview project creation without executing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            target.mkdir()

            with patch("scripts.sprint_lifecycle.Path.home"):
                result = create_project(str(target), dry_run=True)

                # Should not have created structure
                assert not (target / ".claude").exists()

                # Should print dry-run output
                captured = capsys.readouterr()
                assert "[DRY RUN]" in captured.out
                assert result["status"] == "dry-run"

    def test_create_project_already_initialized(self):
        """Should raise error when project already initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / ".claude").mkdir()
            (target / ".claude" / "sprint-steps.json").write_text("{}")

            with pytest.raises(ValidationError, match="already initialized"):
                create_project(str(target))

    def test_create_project_target_not_found(self):
        """Should raise error when target directory doesn't exist."""
        with pytest.raises(FileOperationError, match="not found"):
            create_project("/nonexistent/path")

    def test_create_project_maestro_mode_detection(self):
        """Should detect maestro mode when templates/project/ exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "maestro-project"
            target.mkdir()

            # Create templates/project/ to trigger maestro mode
            (target / "templates" / "project" / ".claude" / "agents").mkdir(
                parents=True
            )
            (target / "templates" / "project" / ".claude" / "hooks").mkdir(parents=True)
            (
                target / "templates" / "project" / ".claude" / "sprint-steps.json"
            ).write_text("{}")
            (target / "templates" / "project" / ".claude" / "settings.json").write_text(
                "{}"
            )
            (target / "templates" / "project" / "CLAUDE.md").write_text("# Template")
            (target / "WORKFLOW_VERSION").write_text("3.1.0")

            # Create existing commands/ and scripts/ (maestro already has these)
            (target / "commands").mkdir()
            (target / "scripts").mkdir()

            result = create_project(str(target))

            # Verify maestro mode was detected
            assert result["maestro_mode"] is True
            assert result["status"] == "initialized"

            # Verify structure created
            assert (target / ".claude" / "agents").exists()
            assert (target / ".claude" / "sprint-steps.json").exists()

            # Verify commands/ and scripts/ were NOT copied (skipped in maestro mode)
            # They already exist from before, but no files should be copied into them
            assert len(list((target / "commands").iterdir())) == 0
            assert len(list((target / "scripts").iterdir())) == 0

    def test_create_project_maestro_mode_copies_from_local_templates(self):
        """Should copy from ./templates/project/ in maestro mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "maestro-project"
            target.mkdir()

            # Create templates/project/ with test content
            template_path = target / "templates" / "project"
            (template_path / ".claude" / "agents").mkdir(parents=True)
            (template_path / ".claude" / "hooks").mkdir(parents=True)
            (template_path / ".claude" / "sprint-steps.json").write_text(
                '{"test": "data"}'
            )
            (template_path / ".claude" / "settings.json").write_text(
                '{"setting": "value"}'
            )

            # Create a test agent file
            (template_path / ".claude" / "agents" / "test-agent.md").write_text(
                "# Test Agent"
            )

            # Create a test hook file
            (template_path / ".claude" / "hooks" / "test_hook.py").write_text(
                "# Test Hook"
            )

            (target / "WORKFLOW_VERSION").write_text("3.1.0")

            result = create_project(str(target))

            # Verify files were copied from local templates
            assert (target / ".claude" / "agents" / "test-agent.md").exists()
            assert (target / ".claude" / "hooks" / "test_hook.py").exists()
            assert (
                target / ".claude" / "sprint-steps.json"
            ).read_text() == '{"test": "data"}'

            # Verify maestro mode flag
            assert result["maestro_mode"] is True

    def test_create_project_normal_mode_uses_global_templates(self):
        """Should copy from ~/.claude/templates/project/ in normal mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "normal-project"
            target.mkdir()

            # Do NOT create templates/project/ - this is normal mode

            with patch("scripts.sprint_lifecycle.Path.home") as mock_home:
                fake_home = Path(tmpdir) / "home"
                fake_home.mkdir()
                mock_home.return_value = fake_home

                # Create master project
                master = fake_home / "Development" / "Dreadnought" / "claude-maestro"
                master.mkdir(parents=True)
                (master / "commands").mkdir()
                (master / "commands" / "test-cmd.md").write_text("# Test")
                (master / "scripts").mkdir()
                (master / "WORKFLOW_VERSION").write_text("3.1.0")

                # Create global templates
                template = fake_home / ".claude" / "templates" / "project"
                (template / ".claude" / "agents").mkdir(parents=True)
                (template / ".claude" / "hooks").mkdir(parents=True)
                (template / ".claude" / "sprint-steps.json").write_text(
                    '{"global": "template"}'
                )
                (template / ".claude" / "settings.json").write_text("{}")
                (template / "CLAUDE.md").write_text("# Global")

                # Create global .claude
                (fake_home / ".claude" / "agents").mkdir(parents=True)
                (fake_home / ".claude" / "hooks").mkdir(parents=True)

                result = create_project(str(target))

                # Verify normal mode (not maestro)
                assert result["maestro_mode"] is False

                # Verify commands/ was copied
                assert (target / "commands" / "test-cmd.md").exists()

                # Verify config came from global templates
                assert (
                    target / ".claude" / "sprint-steps.json"
                ).read_text() == '{"global": "template"}'

    def test_create_project_maestro_mode_command_count_zero(self):
        """Should report 0 commands copied in maestro mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "maestro-project"
            target.mkdir()

            # Create minimal maestro structure
            (target / "templates" / "project" / ".claude" / "agents").mkdir(
                parents=True
            )
            (target / "templates" / "project" / ".claude" / "hooks").mkdir(parents=True)
            (
                target / "templates" / "project" / ".claude" / "sprint-steps.json"
            ).write_text("{}")
            (target / "templates" / "project" / ".claude" / "settings.json").write_text(
                "{}"
            )
            (target / "WORKFLOW_VERSION").write_text("3.1.0")

            result = create_project(str(target))

            # In maestro mode, commands should not be copied
            assert result["command_count"] == 0
            assert result["maestro_mode"] is True


# ============================================================================
# CLI INTEGRATION TESTS
# ============================================================================


class TestCLICommands:
    """Test CLI command parsing and execution."""

    def test_cli_advance_step(self, temp_project, sprint_in_progress, capsys):
        """Test advance-step CLI command."""
        # Create sprint-steps.json
        steps_data = {
            "version": "3.1.0",
            "step_order": ["1.1", "2.1", "2.2", "3.1"],
            "phases": [
                {
                    "phase": 2,
                    "name": "Implementation",
                    "steps": [
                        {"step": "2.1", "name": "Write Tests"},
                        {"step": "2.2", "name": "Implement"},
                    ],
                }
            ],
        }

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project
            (temp_project / ".claude" / "sprint-steps.json").write_text(
                json.dumps(steps_data)
            )

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                with patch("sys.argv", ["sprint_lifecycle.py", "advance-step", "10"]):
                    from scripts.sprint_lifecycle import main

                    main()

        captured = capsys.readouterr()
        assert "advanced to step" in captured.out.lower() or "2.2" in captured.out

    def test_cli_generate_postmortem(self, temp_project, sprint_in_progress, capsys):
        """Test generate-postmortem CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "sys.argv", ["sprint_lifecycle.py", "generate-postmortem", "10"]
            ):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "postmortem" in captured.out.lower()

    def test_cli_sprint_status(self, temp_project, sprint_in_progress, capsys):
        """Test sprint-status CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "sprint-status", "10"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Sprint 10" in captured.out or "Active Sprint" in captured.out

    def test_cli_list_epics(self, temp_project, epic_in_progress, capsys):
        """Test list-epics CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "list-epics"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Epic" in captured.out

    def test_cli_recover_sprint_error(self, temp_project, sprint_in_progress):
        """Test recover-sprint CLI with error handling."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "recover-sprint", "10"]):
                from scripts.sprint_lifecycle import main

                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_cli_no_command(self, capsys):
        """Test CLI with no command shows help."""
        with patch("sys.argv", ["sprint_lifecycle.py"]):
            from scripts.sprint_lifecycle import main

            with pytest.raises(SystemExit):
                main()

        # Help output expected

    def test_cli_start_sprint(self, temp_project, sprint_in_todo, capsys):
        """Test start-sprint CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "start-sprint", "5"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "5" in captured.out or "started" in captured.out.lower()

    def test_cli_abort_sprint(self, temp_project, sprint_in_progress, capsys):
        """Test abort-sprint CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "sys.argv", ["sprint_lifecycle.py", "abort-sprint", "10", "test reason"]
            ):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "abort" in captured.out.lower() or "10" in captured.out

    def test_cli_block_sprint(self, temp_project, sprint_in_progress, capsys):
        """Test block-sprint CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "sys.argv",
                ["sprint_lifecycle.py", "block-sprint", "10", "waiting for API"],
            ):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "block" in captured.out.lower() or "10" in captured.out

    def test_cli_resume_sprint(self, temp_project):
        """Test resume-sprint CLI command."""
        # Create blocked sprint
        sprint_dir = temp_project / "docs" / "sprints" / "2-in-progress"
        sprint_file = sprint_dir / "sprint-15_blocked-sprint--blocked.md"
        sprint_file.write_text(
            "---\nsprint: 15\ntitle: Blocked\nstatus: in-progress\nblocker: test\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "resume-sprint", "15"]):
                from scripts.sprint_lifecycle import main

                main()

    def test_cli_start_epic(self, temp_project, capsys):
        """Test start-epic CLI command."""
        # Create epic in todo
        epic_dir = temp_project / "docs" / "sprints" / "1-todo" / "epic-05_test-epic"
        epic_dir.mkdir(parents=True)
        (epic_dir / "_epic.md").write_text(
            "---\nepic: 5\ntitle: Test\nstatus: todo\n---\n# Epic"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "start-epic", "5"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "5" in captured.out or "epic" in captured.out.lower()

    def test_cli_complete_epic(self, temp_project, capsys):
        """Test complete-epic CLI command."""
        # Create epic with all sprints done
        epic_dir = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-06_complete-epic"
        )
        epic_dir.mkdir(parents=True)
        (epic_dir / "_epic.md").write_text(
            "---\nepic: 6\ntitle: Complete\nstatus: in-progress\n---\n# Epic"
        )
        (epic_dir / "sprint-100_done--done.md").write_text(
            "---\nsprint: 100\ntitle: Done\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "complete-epic", "6"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "6" in captured.out or "complete" in captured.out.lower()

    def test_cli_archive_epic(self, temp_project, capsys):
        """Test archive-epic CLI command."""
        # Create epic in done
        epic_dir = temp_project / "docs" / "sprints" / "3-done" / "epic-07_archive-epic"
        epic_dir.mkdir(parents=True)
        (epic_dir / "_epic.md").write_text(
            "---\nepic: 7\ntitle: Archive\nstatus: done\n---\n# Epic"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "archive-epic", "7"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "7" in captured.out or "archive" in captured.out.lower()

    def test_cli_epic_status(self, temp_project, epic_in_progress, capsys):
        """Test epic-status CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "epic-status", "3"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Epic" in captured.out or "3" in captured.out

    def test_cli_add_to_epic(self, temp_project, epic_in_progress, capsys):
        """Test add-to-epic CLI command."""
        # Create standalone sprint
        sprint_file = (
            temp_project / "docs" / "sprints" / "1-todo" / "sprint-50_standalone.md"
        )
        sprint_file.write_text(
            "---\nsprint: 50\ntitle: Standalone\nepic: null\n---\n# Sprint"
        )

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "add-to-epic", "50", "3"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "50" in captured.out or "3" in captured.out

    def test_cli_register_sprint(self, temp_project, capsys):
        """Test register-sprint CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "sys.argv",
                [
                    "sprint_lifecycle.py",
                    "register-sprint",
                    "New Sprint",
                    "--estimated-hours",
                    "5",
                ],
            ):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Registered" in captured.out or "sprint" in captured.out.lower()

    def test_cli_register_epic(self, temp_project, capsys):
        """Test register-epic CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "sys.argv",
                [
                    "sprint_lifecycle.py",
                    "register-epic",
                    "New Epic",
                    "--sprint-count",
                    "3",
                ],
            ):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Registered" in captured.out or "epic" in captured.out.lower()

    def test_cli_next_sprint_number(self, temp_project, capsys):
        """Test next-sprint-number CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "next-sprint-number"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Next sprint number" in captured.out or "7" in captured.out

    def test_cli_next_epic_number(self, temp_project, capsys):
        """Test next-epic-number CLI command."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("sys.argv", ["sprint_lifecycle.py", "next-epic-number"]):
                from scripts.sprint_lifecycle import main

                main()

        captured = capsys.readouterr()
        assert "Next epic number" in captured.out or "2" in captured.out

    def test_cli_create_project(self, temp_project, capsys):
        """Test create-project CLI command with dry-run."""
        with patch("sys.argv", ["sprint_lifecycle.py", "create-project", "--dry-run"]):
            from scripts.sprint_lifecycle import main

            main()

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out or "project" in captured.out.lower()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test error handling across functions."""

    def test_start_sprint_not_found(self, temp_project):
        """Test start_sprint with non-existent sprint."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                start_sprint(999, dry_run=False)

    def test_abort_sprint_not_found(self, temp_project):
        """Test abort_sprint with non-existent sprint."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                abort_sprint(999, "test reason", dry_run=False)

    def test_block_sprint_not_found(self, temp_project):
        """Test block_sprint with non-existent sprint."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                block_sprint(999, "test blocker", dry_run=False)

    def test_get_sprint_status_no_state(self, temp_project):
        """Test get_sprint_status when state file doesn't exist."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="No state file"):
                get_sprint_status(999)

    def test_advance_step_missing_current_step(self, temp_project, sprint_in_progress):
        """Test advance_step when state is missing current_step."""
        # Corrupt state file
        state_file = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_file) as f:
            state = json.load(f)
        del state["current_step"]
        with open(state_file, "w") as f:
            json.dump(state, f)

        steps_data = {"version": "3.1.0", "step_order": ["1.1"], "phases": []}
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project
            (temp_project / ".claude" / "sprint-steps.json").write_text(
                json.dumps(steps_data)
            )

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                with pytest.raises(ValidationError, match="missing current_step"):
                    advance_step(10, dry_run=False)

    def test_advance_step_at_final_step(self, temp_project, sprint_in_progress):
        """Test advance_step when already at final step."""
        # Set sprint to final step
        state_file = temp_project / ".claude" / "sprint-10-state.json"
        with open(state_file) as f:
            state = json.load(f)
        state["current_step"] = "4.1"  # Final step
        with open(state_file, "w") as f:
            json.dump(state, f)

        steps_data = {
            "version": "3.1.0",
            "step_order": ["1.1", "2.1", "3.1", "4.1"],
            "phases": [],
        }
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project
            (temp_project / ".claude" / "sprint-steps.json").write_text(
                json.dumps(steps_data)
            )

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                with pytest.raises(ValidationError, match="final step|sprint-complete"):
                    advance_step(10, dry_run=False)

    def test_advance_step_no_steps_file(self, temp_project, sprint_in_progress):
        """Test advance_step when sprint-steps.json doesn't exist."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_project

            with patch(
                "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
            ):
                with pytest.raises(
                    FileOperationError, match="Sprint steps definition not found"
                ):
                    advance_step(10, dry_run=False)

    def test_generate_postmortem_without_state(self, temp_project, sprint_in_progress):
        """Test generate_postmortem when state file doesn't exist."""
        # Remove state file
        state_file = temp_project / ".claude" / "sprint-10-state.json"
        state_file.unlink()

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            # Should still work, just without metrics
            result = generate_postmortem(10, dry_run=False)
            assert result["sprint_num"] == 10
            assert result["metrics"] == {}

    def test_start_epic_not_found(self, temp_project):
        """Test start_epic with non-existent epic."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                start_epic(999, dry_run=False)

    def test_complete_epic_not_found(self, temp_project):
        """Test complete_epic with non-existent epic."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                complete_epic(999, dry_run=False)

    def test_archive_epic_not_found(self, temp_project):
        """Test archive_epic with non-existent epic."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="not found"):
                archive_epic(999, dry_run=False)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_full_sprint_lifecycle(self, mock_run, mock_clean, temp_project):
        """Test complete sprint lifecycle: start → work → complete."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        # Create sprint in todo
        sprint_path = (
            temp_project / "docs" / "sprints" / "1-todo" / "sprint-99_lifecycle-test.md"
        )
        sprint_path.write_text("""---
sprint: 99
title: Lifecycle Test
status: todo
created: 2025-12-30
---

# Sprint 99: Lifecycle Test

## Postmortem
Done.
""")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            # 1. Start sprint
            start_result = start_sprint(99)
            assert start_result["sprint_num"] == 99

            # 2. Complete sprint
            complete_sprint(99)

            # Verify final state
            done_path = (
                temp_project
                / "docs"
                / "sprints"
                / "3-done"
                / "_standalone"
                / "sprint-99_lifecycle-test--done.md"
            )
            assert done_path.exists()

            # Verify registry
            registry_path = temp_project / "docs" / "sprints" / "registry.json"
            with open(registry_path) as f:
                registry = json.load(f)
            assert "99" in registry["sprints"]
            assert registry["sprints"]["99"]["status"] == "done"

    def test_epic_with_multiple_sprints(self, temp_project):
        """Test epic management with multiple sprints."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            # Create epic in todo
            epic_dir = (
                temp_project / "docs" / "sprints" / "1-todo" / "epic-99_multi-sprint"
            )
            epic_dir.mkdir()
            (epic_dir / "_epic.md").write_text(
                "---\nepic: 99\ntitle: Multi Sprint\n---\n# Epic"
            )
            (epic_dir / "sprint-01_first.md").write_text("# Sprint 1")
            (epic_dir / "sprint-02_second.md").write_text("# Sprint 2")

            # Start epic
            start_epic(99)

            # Verify moved to in-progress
            in_progress_path = (
                temp_project
                / "docs"
                / "sprints"
                / "2-in-progress"
                / "epic-99_multi-sprint"
            )
            assert in_progress_path.exists()
            assert (in_progress_path / "sprint-01_first.md").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
