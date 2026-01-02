"""Tests for sprint_lifecycle.py automation utilities.

These tests validate:
1. Project root finding from various working directories
2. Sprint file movement (epic vs standalone)
3. Registry updates with atomic operations
4. Epic completion detection
5. Git tagging with auto-push
6. Dry-run mode for all operations
7. Error handling and rollback on failure
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from sprint_lifecycle.py
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sprint_lifecycle import (
    find_project_root,
    move_to_done,
    update_registry,
    check_epic_completion,
    create_git_tag,
    check_git_clean,
    _find_sprint_file,
    _is_epic_sprint,
    _update_yaml_frontmatter,
    GitError,
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
        (project_root / "scripts").mkdir()

        yield project_root


@pytest.fixture
def sprint_file_standalone(temp_project):
    """Create a standalone sprint file in 2-in-progress."""
    sprint_path = (
        temp_project / "docs" / "sprints" / "2-in-progress" / "sprint-05_test-sprint.md"
    )
    content = """---
sprint: 5
title: Test Sprint
status: in-progress
workflow_version: "2.1"
epic: null
created: 2025-12-30
started: 2025-12-30T10:00:00Z
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
def sprint_file_epic(temp_project):
    """Create an epic sprint file."""
    epic_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-02_test-epic"
    epic_dir.mkdir()

    sprint_path = epic_dir / "sprint-10_epic-sprint.md"
    content = """---
sprint: 10
title: Epic Sprint
status: in-progress
workflow_version: "2.1"
epic: 2
created: 2025-12-30
started: 2025-12-30T10:00:00Z
completed: null
hours: null
---

# Sprint 10: Epic Sprint

## Overview
Test epic sprint.
"""
    sprint_path.write_text(content)

    # Create sprint-11 (not done yet)
    sprint_11_path = epic_dir / "sprint-11_another-sprint.md"
    sprint_11_content = """---
sprint: 11
title: Another Sprint
status: in-progress
epic: 2
---

# Sprint 11
"""
    sprint_11_path.write_text(sprint_11_content)

    # Create epic metadata file
    epic_file = epic_dir / "_epic.md"
    epic_file.write_text(
        "# Epic 02: Test Epic\n\n## Sprints\n- Sprint 10\n- Sprint 11\n"
    )

    return sprint_path


class TestFindProjectRoot:
    """Test project root finding functionality."""

    def test_find_from_root(self, temp_project):
        """Should find project root when already at root."""
        with patch("pathlib.Path.cwd", return_value=temp_project):
            root = find_project_root()
            # Resolve both paths to handle symlinks (/var -> /private/var on macOS)
            assert root.resolve() == temp_project.resolve()

    def test_find_from_subdirectory(self, temp_project):
        """Should find project root when in subdirectory."""
        subdir = temp_project / "docs" / "sprints"
        with patch("pathlib.Path.cwd", return_value=subdir):
            root = find_project_root()
            # Resolve both paths to handle symlinks (/var -> /private/var on macOS)
            assert root.resolve() == temp_project.resolve()

    def test_find_from_deep_subdirectory(self, temp_project):
        """Should find project root when in deep subdirectory."""
        deep_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-01_test"
        deep_dir.mkdir(parents=True)
        with patch("pathlib.Path.cwd", return_value=deep_dir):
            root = find_project_root()
            # Resolve both paths to handle symlinks (/var -> /private/var on macOS)
            assert root.resolve() == temp_project.resolve()

    def test_error_when_no_claude_dir(self):
        """Should raise error when no .claude/ directory found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                with pytest.raises(
                    FileOperationError, match="Could not find project root"
                ):
                    find_project_root()


class TestFindSprintFile:
    """Test sprint file finding functionality."""

    def test_find_standalone_sprint(self, temp_project, sprint_file_standalone):
        """Should find standalone sprint file."""
        found = _find_sprint_file(5, temp_project)
        assert found == sprint_file_standalone

    def test_find_epic_sprint(self, temp_project, sprint_file_epic):
        """Should find sprint file inside epic folder."""
        found = _find_sprint_file(10, temp_project)
        assert found == sprint_file_epic

    def test_not_found_returns_none(self, temp_project):
        """Should return None when sprint doesn't exist."""
        found = _find_sprint_file(999, temp_project)
        assert found is None


class TestIsEpicSprint:
    """Test epic sprint detection."""

    def test_detects_epic_sprint(self, temp_project, sprint_file_epic):
        """Should detect sprint is part of epic."""
        is_epic, epic_num = _is_epic_sprint(sprint_file_epic)
        assert is_epic is True
        assert epic_num == 2

    def test_detects_standalone_sprint(self, temp_project, sprint_file_standalone):
        """Should detect sprint is standalone."""
        is_epic, epic_num = _is_epic_sprint(sprint_file_standalone)
        assert is_epic is False
        assert epic_num is None

    def test_extracts_epic_number(self, temp_project):
        """Should correctly extract epic number from path."""
        path = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-15_big-epic"
            / "sprint-01_test.md"
        )
        is_epic, epic_num = _is_epic_sprint(path)
        assert is_epic is True
        assert epic_num == 15


class TestUpdateYamlFrontmatter:
    """Test YAML frontmatter updating."""

    def test_update_existing_field(self, temp_project):
        """Should update existing frontmatter field."""
        test_file = temp_project / "test.md"
        test_file.write_text("""---
status: in-progress
hours: null
---

# Content
""")

        _update_yaml_frontmatter(test_file, {"status": "done", "hours": "5.5"})

        content = test_file.read_text()
        assert "status: done" in content
        assert "hours: 5.5" in content

    def test_add_new_field(self, temp_project):
        """Should add new field to frontmatter."""
        test_file = temp_project / "test.md"
        test_file.write_text("""---
status: in-progress
---

# Content
""")

        _update_yaml_frontmatter(test_file, {"completed": "2025-12-30"})

        content = test_file.read_text()
        assert "completed: 2025-12-30" in content

    def test_error_on_missing_frontmatter(self, temp_project):
        """Should raise error when frontmatter missing."""
        test_file = temp_project / "test.md"
        test_file.write_text("# No frontmatter\n\nContent")

        with pytest.raises(ValidationError, match="missing YAML frontmatter"):
            _update_yaml_frontmatter(test_file, {"status": "done"})

    def test_preserves_body_content(self, temp_project):
        """Should preserve body content when updating frontmatter."""
        test_file = temp_project / "test.md"
        original_body = "\n# Sprint Title\n\n## Overview\nSome content here.\n"
        test_file.write_text(f"---\nstatus: in-progress\n---{original_body}")

        _update_yaml_frontmatter(test_file, {"status": "done"})

        content = test_file.read_text()
        assert "# Sprint Title" in content
        assert "## Overview" in content
        assert "Some content here" in content


class TestMoveToDone:
    """Test sprint file movement to done status."""

    def test_move_standalone_sprint(self, temp_project, sprint_file_standalone):
        """Should move standalone sprint to 3-done/_standalone/."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            new_path = move_to_done(5)

        expected_path = (
            temp_project
            / "docs"
            / "sprints"
            / "3-done"
            / "_standalone"
            / "sprint-05_test-sprint--done.md"
        )
        assert new_path == expected_path
        assert expected_path.exists()
        assert not sprint_file_standalone.exists()

        # Verify YAML frontmatter updated
        content = expected_path.read_text()
        assert "status: done" in content
        # Check that completed field exists (date will be current date)
        assert "completed:" in content
        assert "completed: null" not in content

    def test_rename_epic_sprint_in_place(self, temp_project, sprint_file_epic):
        """Should rename epic sprint with --done suffix in epic folder."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            new_path = move_to_done(10)

        expected_path = sprint_file_epic.parent / "sprint-10_epic-sprint--done.md"
        assert new_path == expected_path
        assert expected_path.exists()
        assert not sprint_file_epic.exists()

        # Verify still in epic folder
        assert "epic-02_test-epic" in str(expected_path)

        # Verify YAML frontmatter updated
        content = expected_path.read_text()
        assert "status: done" in content

    def test_error_when_sprint_not_found(self, temp_project):
        """Should raise error when sprint file doesn't exist."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with pytest.raises(FileOperationError, match="Sprint 999 not found"):
                move_to_done(999)

    def test_error_when_already_done(self, temp_project):
        """Should raise error when sprint already marked done."""
        done_sprint = (
            temp_project
            / "docs"
            / "sprints"
            / "3-done"
            / "_standalone"
            / "sprint-03_old--done.md"
        )
        done_sprint.parent.mkdir(parents=True, exist_ok=True)
        done_sprint.write_text("---\nstatus: done\n---\n# Sprint")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch(
                "scripts.sprint_lifecycle._find_sprint_file", return_value=done_sprint
            ):
                with pytest.raises(ValidationError, match="already marked as done"):
                    move_to_done(3)

    def test_dry_run_mode(self, temp_project, sprint_file_standalone, capsys):
        """Should preview changes without executing in dry-run mode."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            move_to_done(5, dry_run=True)

        # File should not have moved
        assert sprint_file_standalone.exists()

        # Should print dry-run output
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Would move standalone sprint" in captured.out


class TestUpdateRegistry:
    """Test sprint registry updates."""

    def test_create_registry_if_missing(self, temp_project):
        """Should create registry file if it doesn't exist."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            update_registry(5, status="done", completed="2025-12-30", hours=6)

        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        assert registry_path.exists()

        with open(registry_path) as f:
            registry = json.load(f)

        assert "sprints" in registry
        assert "5" in registry["sprints"]
        assert registry["sprints"]["5"]["status"] == "done"
        assert registry["sprints"]["5"]["hours"] == 6

    def test_update_existing_registry(self, temp_project):
        """Should update existing sprint in registry."""
        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        existing = {"version": "1.0", "sprints": {"3": {"status": "in-progress"}}}
        with open(registry_path, "w") as f:
            json.dump(existing, f)

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            update_registry(5, status="done", hours=4.5)

        with open(registry_path) as f:
            registry = json.load(f)

        # Should preserve existing entries
        assert "3" in registry["sprints"]
        assert registry["sprints"]["3"]["status"] == "in-progress"

        # Should add new entry
        assert "5" in registry["sprints"]
        assert registry["sprints"]["5"]["status"] == "done"
        assert registry["sprints"]["5"]["hours"] == 4.5

    def test_dry_run_mode(self, temp_project, capsys):
        """Should preview registry updates in dry-run mode."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            update_registry(5, status="done", hours=3, dry_run=True)

        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        assert not registry_path.exists()

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "status: done" in captured.out
        assert "hours: 3" in captured.out


class TestCheckEpicCompletion:
    """Test epic completion detection."""

    def test_epic_complete_all_done(self, temp_project):
        """Should detect epic is complete when all sprints done."""
        epic_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-03_test"
        epic_dir.mkdir(parents=True)

        # Create done sprints
        (epic_dir / "sprint-01_first--done.md").write_text("# Sprint 1")
        (epic_dir / "sprint-02_second--done.md").write_text("# Sprint 2")
        (epic_dir / "_epic.md").write_text("# Epic 03")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            is_complete, message = check_epic_completion(3)

        assert is_complete is True
        assert "Epic 3 is complete" in message
        assert "Total sprints: 2" in message
        assert "Done: 2" in message

    def test_epic_incomplete_has_active_sprints(self, temp_project):
        """Should detect epic is incomplete when active sprints remain."""
        epic_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-04_test"
        epic_dir.mkdir(parents=True)

        (epic_dir / "sprint-01_first--done.md").write_text("# Sprint 1")
        (epic_dir / "sprint-02_second.md").write_text("# Sprint 2")  # Still active
        (epic_dir / "_epic.md").write_text("# Epic 04")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            is_complete, message = check_epic_completion(4)

        assert is_complete is False
        assert "not complete yet" in message
        assert "Remaining: 1" in message
        assert "sprint-02_second.md" in message

    def test_epic_complete_with_aborted_sprints(self, temp_project):
        """Should consider aborted sprints as finished."""
        epic_dir = temp_project / "docs" / "sprints" / "2-in-progress" / "epic-05_test"
        epic_dir.mkdir(parents=True)

        (epic_dir / "sprint-01_first--done.md").write_text("# Sprint 1")
        (epic_dir / "sprint-02_second--aborted.md").write_text("# Sprint 2")
        (epic_dir / "_epic.md").write_text("# Epic 05")

        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            is_complete, message = check_epic_completion(5)

        assert is_complete is True
        assert "Epic 5 is complete" in message
        assert "Done: 1" in message
        assert "Aborted: 1" in message

    def test_epic_not_found(self, temp_project):
        """Should return error message when epic doesn't exist."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            is_complete, message = check_epic_completion(999)

        assert is_complete is False
        assert "Epic 999 not found" in message


class TestCheckGitClean:
    """Test git status checking."""

    def test_clean_working_directory(self):
        """Should return True when git status is clean."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)
            assert check_git_clean() is True

    def test_dirty_working_directory(self):
        """Should return False when uncommitted changes exist."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=" M file.py\n", returncode=0)
            assert check_git_clean() is False

    def test_error_returns_false(self):
        """Should return False on git command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            assert check_git_clean() is False


class TestCreateGitTag:
    """Test git tag creation."""

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_create_tag_with_push(self, mock_run, mock_clean):
        """Should create annotated tag and push to remote."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        create_git_tag(5, "Test Sprint", auto_push=True)

        # Should have called git tag
        assert mock_run.call_count == 2  # tag + push
        tag_call = mock_run.call_args_list[0]
        assert tag_call[0][0][0:3] == ["git", "tag", "-a"]
        assert "sprint-5" in tag_call[0][0]
        assert "Sprint 5: Test Sprint" in tag_call[0][0]

        # Should have called git push
        push_call = mock_run.call_args_list[1]
        assert push_call[0][0] == ["git", "push", "origin", "sprint-5"]

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_create_tag_without_push(self, mock_run, mock_clean):
        """Should create tag without pushing."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        create_git_tag(5, "Test Sprint", auto_push=False)

        # Should only call git tag, not push
        assert mock_run.call_count == 1
        tag_call = mock_run.call_args_list[0]
        assert "git tag -a" in " ".join(tag_call[0][0])

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=False)
    def test_error_on_dirty_working_tree(self, mock_clean):
        """Should raise error when working directory is dirty."""
        with pytest.raises(ValidationError, match="working directory is dirty"):
            create_git_tag(5, "Test Sprint")

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_dry_run_mode(self, mock_run, mock_clean, capsys):
        """Should preview tag creation in dry-run mode."""
        create_git_tag(5, "Test Sprint", dry_run=True, auto_push=True)

        # Should not have called git
        mock_run.assert_not_called()

        # Should print dry-run output
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "sprint-5" in captured.out
        assert "Auto-push: Yes" in captured.out

    @patch("scripts.sprint_lifecycle.check_git_clean", return_value=True)
    @patch("subprocess.run")
    def test_error_on_git_failure(self, mock_run, mock_clean):
        """Should raise GitError when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="Tag already exists"
        )

        with pytest.raises(GitError, match="Failed to create/push git tag"):
            create_git_tag(5, "Test Sprint")


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_complete_sprint_workflow_standalone(
        self, temp_project, sprint_file_standalone
    ):
        """Test complete workflow for standalone sprint."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("scripts.sprint_lifecycle.check_git_clean", return_value=True):
                with patch("subprocess.run") as mock_git:
                    mock_git.return_value = Mock(returncode=0, stderr="")

                    # Move to done
                    new_path = move_to_done(5)
                    assert "--done" in str(new_path)
                    assert "_standalone" in str(new_path)

                    # Update registry
                    update_registry(5, status="done", completed="2025-12-30", hours=6)

                    # Create tag
                    create_git_tag(5, "Test Sprint", auto_push=True)

        # Verify file moved
        assert new_path.exists()

        # Verify registry updated
        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        assert registry["sprints"]["5"]["status"] == "done"

        # Verify git tag created
        assert mock_git.call_count == 2  # tag + push

    def test_complete_sprint_workflow_epic(self, temp_project, sprint_file_epic):
        """Test complete workflow for epic sprint."""
        with patch(
            "scripts.sprint_lifecycle.find_project_root", return_value=temp_project
        ):
            with patch("scripts.sprint_lifecycle.check_git_clean", return_value=True):
                with patch("subprocess.run") as mock_git:
                    mock_git.return_value = Mock(returncode=0, stderr="")

                    # Move to done (stays in epic folder)
                    new_path = move_to_done(10)
                    assert "--done" in str(new_path)
                    assert "epic-02_test-epic" in str(new_path)

                    # Update registry
                    update_registry(10, status="done", hours=5)

                    # Check epic completion
                    is_complete, msg = check_epic_completion(2)
                    assert is_complete is False  # Still has sprint-11

                    # Create tag
                    create_git_tag(10, "Epic Sprint")

        # Verify file renamed in epic folder
        assert new_path.exists()
        assert new_path.parent.name == "epic-02_test-epic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
