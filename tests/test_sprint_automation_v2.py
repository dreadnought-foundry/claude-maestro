"""Tests for sprint_automation modular package.

These tests mirror test_sprint_lifecycle.py but use the v2 modular package.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from v2 modular package
from scripts.sprint_automation import (
    find_project_root,
    move_to_done,
    update_registry,
    create_git_tag,
    check_git_clean,
    find_sprint_file,
    is_epic_sprint,
    update_yaml_frontmatter,
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
Test sprint inside an epic.
"""
    sprint_path.write_text(content)
    return sprint_path


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_find_from_root(self, temp_project, monkeypatch):
        """Should find project root when already in root."""
        monkeypatch.chdir(temp_project)
        # Use resolve() to handle macOS /var -> /private/var symlinks
        assert find_project_root().resolve() == temp_project.resolve()

    def test_find_from_subdirectory(self, temp_project, monkeypatch):
        """Should find project root from any subdirectory."""
        subdir = temp_project / "docs" / "sprints"
        monkeypatch.chdir(subdir)
        assert find_project_root().resolve() == temp_project.resolve()

    def test_find_from_deep_subdirectory(self, temp_project, monkeypatch):
        """Should find project root from deeply nested directory."""
        deep_subdir = temp_project / "docs" / "sprints" / "2-in-progress"
        monkeypatch.chdir(deep_subdir)
        assert find_project_root().resolve() == temp_project.resolve()


class TestFindSprintFile:
    """Tests for find_sprint_file function."""

    def test_find_standalone_sprint(self, temp_project, sprint_file_standalone):
        """Should find standalone sprint file."""
        result = find_sprint_file(5, temp_project)
        assert result == sprint_file_standalone

    def test_find_epic_sprint(self, temp_project, sprint_file_epic):
        """Should find sprint file inside epic folder."""
        result = find_sprint_file(10, temp_project)
        assert result == sprint_file_epic

    def test_not_found_returns_none(self, temp_project):
        """Should return None when sprint not found."""
        result = find_sprint_file(999, temp_project)
        assert result is None


class TestIsEpicSprint:
    """Tests for is_epic_sprint function."""

    def test_detects_epic_sprint(self, temp_project, sprint_file_epic):
        """Should detect sprint is in epic folder."""
        is_epic, epic_num = is_epic_sprint(sprint_file_epic)
        assert is_epic is True
        assert epic_num == 2

    def test_detects_standalone_sprint(self, temp_project, sprint_file_standalone):
        """Should detect sprint is standalone."""
        is_epic, epic_num = is_epic_sprint(sprint_file_standalone)
        assert is_epic is False
        assert epic_num is None

    def test_extracts_epic_number(self, temp_project):
        """Should correctly extract epic number from path."""
        epic_dir = (
            temp_project / "docs" / "sprints" / "2-in-progress" / "epic-15_some-epic"
        )
        epic_dir.mkdir()
        sprint_path = epic_dir / "sprint-20_test.md"
        sprint_path.write_text("---\ntitle: test\n---\n")

        is_epic, epic_num = is_epic_sprint(sprint_path)
        assert is_epic is True
        assert epic_num == 15


class TestUpdateYamlFrontmatter:
    """Tests for update_yaml_frontmatter function."""

    def test_update_existing_field(self, temp_project, sprint_file_standalone):
        """Should update existing YAML field."""
        update_yaml_frontmatter(sprint_file_standalone, {"status": "done"})

        content = sprint_file_standalone.read_text()
        assert "status: done" in content

    def test_add_new_field(self, temp_project, sprint_file_standalone):
        """Should add new YAML field."""
        update_yaml_frontmatter(sprint_file_standalone, {"new_field": "value"})

        content = sprint_file_standalone.read_text()
        assert "new_field: value" in content

    def test_preserves_body_content(self, temp_project, sprint_file_standalone):
        """Should preserve markdown body after frontmatter."""
        update_yaml_frontmatter(sprint_file_standalone, {"status": "done"})

        content = sprint_file_standalone.read_text()
        assert "## Overview" in content
        assert "Test sprint for automation." in content


class TestMoveToDone:
    """Tests for move_to_done function."""

    def test_move_standalone_sprint(
        self, temp_project, sprint_file_standalone, monkeypatch
    ):
        """Should move standalone sprint to done folder."""
        monkeypatch.chdir(temp_project)

        new_path = move_to_done(5, dry_run=False)

        assert new_path.exists()
        assert "3-done" in str(new_path)
        assert "--done" in new_path.name
        assert not sprint_file_standalone.exists()

    def test_rename_epic_sprint_in_place(
        self, temp_project, sprint_file_epic, monkeypatch
    ):
        """Should rename epic sprint in place (stay in epic folder)."""
        monkeypatch.chdir(temp_project)

        new_path = move_to_done(10, dry_run=False)

        assert new_path.exists()
        assert "epic-02_test-epic" in str(new_path)
        assert "--done" in new_path.name

    def test_dry_run_mode(self, temp_project, sprint_file_standalone, monkeypatch):
        """Should not move file in dry run mode."""
        monkeypatch.chdir(temp_project)

        new_path = move_to_done(5, dry_run=True)

        assert sprint_file_standalone.exists()
        assert not new_path.exists()


class TestCheckGitClean:
    """Tests for check_git_clean function."""

    def test_clean_working_directory(self):
        """Should return True when git status is clean."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")
            assert check_git_clean() is True

    def test_dirty_working_directory(self):
        """Should return False when git status has changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="M some_file.py")
            assert check_git_clean() is False


class TestCreateGitTag:
    """Tests for create_git_tag function."""

    def test_create_tag_with_push(self, temp_project, monkeypatch):
        """Should create and push tag."""
        monkeypatch.chdir(temp_project)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")

            # Note: signature is create_git_tag(sprint_num, title, dry_run, auto_push)
            create_git_tag(5, "Test Sprint", dry_run=False, auto_push=True)

            # Should call git tag and git push
            assert mock_run.call_count >= 2

    def test_dry_run_mode(self, temp_project, monkeypatch):
        """Should not create tag in dry run mode."""
        monkeypatch.chdir(temp_project)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")

            create_git_tag(5, "Test Sprint", dry_run=True, auto_push=False)

            # In dry run mode, fewer git commands are called


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_complete_sprint_workflow_standalone(
        self, temp_project, sprint_file_standalone, monkeypatch
    ):
        """Test complete workflow for standalone sprint."""
        monkeypatch.chdir(temp_project)

        # Create registry (path is docs/sprints/registry.json)
        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        registry_data = {
            "sprints": {"5": {"title": "Test Sprint", "status": "in-progress"}},
            "epics": {},
        }
        registry_path.write_text(json.dumps(registry_data))

        # Move to done
        new_path = move_to_done(5, dry_run=False)
        assert new_path.exists()
        assert "--done" in new_path.name

        # Update registry - signature is (sprint_num, status, dry_run, **metadata)
        update_registry(5, "done", dry_run=False, completed="2025-12-30")

        # Verify registry updated
        registry = json.loads(registry_path.read_text())
        assert registry["sprints"]["5"]["status"] == "done"

    def test_complete_sprint_workflow_epic(
        self, temp_project, sprint_file_epic, monkeypatch
    ):
        """Test complete workflow for epic sprint."""
        monkeypatch.chdir(temp_project)

        # Create done folder for epic
        epic_done_dir = (
            temp_project / "docs" / "sprints" / "3-done" / "epic-02_test-epic"
        )
        epic_done_dir.mkdir(parents=True)

        # Create registry (path is docs/sprints/registry.json)
        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        registry_data = {
            "sprints": {
                "10": {"title": "Epic Sprint", "status": "in-progress", "epic": 2}
            },
            "epics": {"2": {"title": "Test Epic", "sprints": [10]}},
        }
        registry_path.write_text(json.dumps(registry_data))

        # Move to done
        new_path = move_to_done(10, dry_run=False)
        assert new_path.exists()
        assert "--done" in new_path.name

        # Update registry - signature is (sprint_num, status, dry_run, **metadata)
        update_registry(10, "done", dry_run=False)

        # Verify registry
        registry = json.loads(registry_path.read_text())
        assert registry["sprints"]["10"]["status"] == "done"
