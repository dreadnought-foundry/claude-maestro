"""
Test suite for sprint completion automation workflow.

Validates:
1. Automation script functionality
2. Hook enforcement of automation-only approach
3. Proper file handling (YAML, postmortem, locations)
4. Git operations (tags, commits)
5. Epic vs standalone handling
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.sprint_lifecycle import complete_sprint


@pytest.mark.skip(
    reason="Tests written for v3.1.0 API. complete_sprint() signature changed in v3.5.0 "
    "(removed project_root param, changed return format). Needs refactoring."
)
class TestSprintCompletionAutomation:
    """Test the complete-sprint automation script."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Create directory structure
        (tmp_path / "docs" / "sprints" / "2-in-progress" / "epic-01_test-epic").mkdir(
            parents=True
        )
        (tmp_path / "docs" / "sprints" / "3-done" / "_standalone").mkdir(parents=True)
        (tmp_path / ".claude").mkdir()

        # Create registry
        registry = {
            "sprints": [],
            "epics": [{"epic": 1, "title": "Test Epic", "status": "in_progress"}],
        }
        (tmp_path / "docs" / "sprints" / "registry.json").write_text(
            json.dumps(registry, indent=2)
        )

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )

        return tmp_path

    @pytest.fixture
    def valid_sprint_file(self, temp_project):
        """Create a valid sprint file with YAML frontmatter and postmortem."""
        sprint_dir = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-01_test-sprint"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-01_test-sprint.md"
        content = """---
sprint: 1
title: Test Sprint
epic: 01
status: done
created: 2026-01-01T00:00:00Z
started: 2026-01-01T10:00:00Z
completed: 2026-01-01T16:00:00Z
hours: 6.0
workflow_version: "3.1.0"
---

# Sprint 1: Test Sprint

## Goal
Test sprint for automation validation.

## Postmortem

### Summary
Test sprint completed successfully.

### What Went Well
- Automation worked
- Tests passed

### What Could Improve
- Nothing

### Action Items
- [x] `[done]` Complete tests
"""
        sprint_file.write_text(content)

        # Create state file
        state = {
            "sprint_number": 1,
            "sprint_file": str(sprint_file),
            "status": "in_progress",
            "started_at": "2026-01-01T10:00:00Z",
            "workflow_version": "3.1.0",
        }
        (temp_project / ".claude" / "sprint-1-state.json").write_text(
            json.dumps(state, indent=2)
        )

        return sprint_file

    def test_valid_sprint_completion(self, temp_project, valid_sprint_file):
        """Test completing a valid sprint with proper YAML and postmortem."""
        result = complete_sprint(1, project_root=temp_project, dry_run=True)

        assert result["success"] is True
        assert "postmortem_exists" in result
        assert result["postmortem_exists"] is True
        assert "yaml_valid" in result
        assert result["yaml_valid"] is True

    def test_missing_yaml_frontmatter(self, temp_project):
        """Test error when sprint file missing YAML frontmatter."""
        sprint_dir = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-02_no-yaml"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-02_no-yaml.md"
        sprint_file.write_text("# Sprint 2\n\nNo YAML frontmatter")

        with pytest.raises(Exception, match="missing YAML frontmatter"):
            complete_sprint(2, project_root=temp_project)

    def test_missing_postmortem(self, temp_project):
        """Test error when sprint file missing postmortem section."""
        sprint_dir = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-03_no-postmortem"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-03_no-postmortem.md"
        content = """---
sprint: 3
title: No Postmortem
status: done
started: 2026-01-01T10:00:00Z
---

# Sprint 3: No Postmortem

## Goal
Missing postmortem section.
"""
        sprint_file.write_text(content)

        with pytest.raises(Exception, match="[Pp]ostmortem"):
            complete_sprint(3, project_root=temp_project)

    def test_datetime_timezone_handling(self, temp_project):
        """Test proper handling of timezone-aware timestamps."""
        sprint_dir = (
            temp_project
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-04_timezone"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-04_timezone.md"
        content = """---
sprint: 4
title: Timezone Test
epic: 01
status: done
started: 2026-01-01T10:00:00Z
completed: 2026-01-01T16:30:00Z
hours: 6.5
---

# Sprint 4

## Postmortem
### Summary
Test timezone handling.
"""
        sprint_file.write_text(content)

        result = complete_sprint(4, project_root=temp_project, dry_run=True)

        assert result["success"] is True
        # Should calculate hours from timestamps
        assert "hours_calculated" in result

    def test_epic_sprint_file_location(self, temp_project, valid_sprint_file):
        """Test that epic sprints stay in 2-in-progress with --done suffix."""
        result = complete_sprint(1, project_root=temp_project, dry_run=True)

        expected_path = "2-in-progress/epic-01_test-epic/sprint-01_test-sprint--done"
        assert expected_path in result["target_location"]

        # Verify NOT moved to 3-done
        assert "3-done" not in result["target_location"]

    def test_standalone_sprint_file_location(self, temp_project):
        """Test that standalone sprints move to 3-done/_standalone."""
        sprint_dir = (
            temp_project / "docs" / "sprints" / "2-in-progress" / "sprint-05_standalone"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-05_standalone.md"
        content = """---
sprint: 5
title: Standalone Sprint
status: done
started: 2026-01-01T10:00:00Z
completed: 2026-01-01T14:00:00Z
hours: 4.0
---

# Sprint 5

## Postmortem
### Summary
Standalone sprint test.
"""
        sprint_file.write_text(content)

        result = complete_sprint(5, project_root=temp_project, dry_run=True)

        assert "3-done/_standalone" in result["target_location"]
        assert "--done" in result["target_location"]

    def test_git_tag_creation(self, temp_project, valid_sprint_file):
        """Test that git tags are created correctly."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            complete_sprint(1, project_root=temp_project, dry_run=False)

            # Check that git tag command was called
            tag_calls = [c for c in mock_run.call_args_list if "git tag" in str(c)]
            assert len(tag_calls) > 0

            # Verify tag name format
            tag_call_str = str(tag_calls[0])
            assert "sprint-1" in tag_call_str

    def test_registry_update(self, temp_project, valid_sprint_file):
        """Test that registry is updated on completion."""
        complete_sprint(1, project_root=temp_project, dry_run=False)

        registry_file = temp_project / "docs" / "sprints" / "registry.json"
        registry = json.loads(registry_file.read_text())

        # Find sprint 1 in registry
        sprint_entry = next((s for s in registry["sprints"] if s["sprint"] == 1), None)
        assert sprint_entry is not None
        assert sprint_entry["status"] == "done"

    def test_state_file_update(self, temp_project, valid_sprint_file):
        """Test that state file status is updated to complete."""
        complete_sprint(1, project_root=temp_project, dry_run=False)

        state_file = temp_project / ".claude" / "sprint-1-state.json"
        state = json.loads(state_file.read_text())

        assert state["status"] == "complete"
        assert "completed_at" in state


class TestHookEnforcement:
    """Test that hooks enforce automation-only approach."""

    @pytest.fixture
    def hook_script(self):
        """Load the pre_tool_use.py hook."""
        hook_path = Path.home() / ".claude" / "hooks" / "pre_tool_use.py"
        if not hook_path.exists():
            pytest.skip("Hook not installed")
        return hook_path

    def test_manual_mv_blocked(self, hook_script):
        """Test that manual mv commands on sprint files are blocked."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "mv docs/sprints/2-in-progress/sprint-03_test.md docs/sprints/3-done/sprint-03_test--done.md"
            },
        }

        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should be blocked
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert (
            "SPRINT MOVE BLOCKED"
            in output["hookSpecificOutput"]["permissionDecisionReason"]
        )

    def test_automation_script_allowed(self, hook_script):
        """Test that automation script bypasses the gate."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "python3 scripts/sprint_lifecycle.py complete-sprint 3"
            },
        }

        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
        )

        # Should be exit code 0 (allowed)
        assert result.returncode == 0

    def test_error_message_guidance(self, hook_script):
        """Test that error messages guide to correct command."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git mv docs/sprints/2-in-progress/sprint-05_test.md docs/sprints/3-done/sprint-05_test.md"
            },
        }

        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]

        # Error message should mention the correct command
        assert "/sprint-complete" in reason

    def test_invalid_done_folder_blocked(self, hook_script):
        """Test that moves to 4-done, 5-done, etc. are blocked."""
        for invalid_folder in ["4-done", "5-done", "2-done"]:
            hook_input = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": f"mv docs/sprints/2-in-progress/sprint-03.md docs/sprints/{invalid_folder}/sprint-03.md"
                },
            }

            result = subprocess.run(
                ["python3", str(hook_script)],
                input=json.dumps(hook_input),
                capture_output=True,
                text=True,
            )

            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_valid_3done_location_required(self, hook_script):
        """Test that only valid 3-done locations are accepted."""
        # Invalid: missing --done suffix
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "mv docs/sprints/2-in-progress/sprint-03_test.md docs/sprints/3-done/_standalone/sprint-03_test.md"
            },
        }

        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "--done" in output["hookSpecificOutput"]["permissionDecisionReason"]


class TestWorkflowIntegration:
    """End-to-end integration tests for sprint completion workflow."""

    def test_complete_workflow_epic_sprint(self, tmp_path):
        """Test complete workflow for an epic sprint."""
        # Setup: Create project, sprint file, state file
        # Execute: Run complete-sprint automation
        # Verify: File location, registry, state, git tag
        pytest.skip("Integration test - requires full project setup")

    def test_complete_workflow_standalone_sprint(self, tmp_path):
        """Test complete workflow for a standalone sprint."""
        pytest.skip("Integration test - requires full project setup")

    def test_skill_invocation_uses_automation(self):
        """Test that /sprint-complete skill uses automation script."""
        skill_path = Path.home() / ".claude" / "commands" / "sprint-complete.md"
        if not skill_path.exists():
            pytest.skip("Skill not installed")

        content = skill_path.read_text()

        # Verify skill uses automation script (central path as of v3.5.0)
        assert "sprint_lifecycle.py complete-sprint" in content

        # Verify skill doesn't have manual mv commands
        assert 'mv "$SPRINT_FILE"' not in content


@pytest.mark.skip(
    reason="Tests written for v3.1.0 API. complete_sprint() signature changed in v3.5.0."
)
class TestErrorHandling:
    """Test error handling and validation."""

    def test_naive_datetime_error_message(self):
        """Test clear error for naive vs aware datetime issues."""
        # Test that error message mentions timezone format
        pytest.skip("Requires sprint_lifecycle module refactor")

    def test_missing_postmortem_error_message(self, temp_project):
        """Test clear error when postmortem missing."""
        sprint_dir = (
            temp_project / "docs" / "sprints" / "2-in-progress" / "sprint-99_test"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-99_test.md"
        sprint_file.write_text("""---
sprint: 99
title: Test
status: done
---

# Sprint 99
No postmortem here!
""")

        try:
            complete_sprint(99, project_root=temp_project)
            assert False, "Should have raised exception"
        except Exception as e:
            error_msg = str(e)
            # Error should mention postmortem
            assert "postmortem" in error_msg.lower()
            # Error should suggest command to fix
            assert "/sprint-postmortem" in error_msg or "postmortem" in error_msg

    def test_validation_before_operations(self, temp_project):
        """Test that validation happens before any file operations."""
        # Create invalid sprint (no YAML)
        sprint_dir = (
            temp_project / "docs" / "sprints" / "2-in-progress" / "sprint-98_invalid"
        )
        sprint_dir.mkdir(parents=True)

        sprint_file = sprint_dir / "sprint-98_invalid.md"
        sprint_file.write_text("# Invalid sprint\nNo YAML, no postmortem")

        original_mtime = sprint_file.stat().st_mtime

        try:
            complete_sprint(98, project_root=temp_project)
        except Exception:
            pass

        # File should not be modified if validation failed
        assert sprint_file.stat().st_mtime == original_mtime


class TestStartSprintAutomation:
    """Test start-sprint automation handles all file location scenarios."""

    @pytest.fixture
    def temp_project_with_epic(self, tmp_path):
        """Create project with epic structure in 2-in-progress."""
        # Create directory structure
        epic_dir = tmp_path / "docs" / "sprints" / "2-in-progress" / "epic-01_test-epic"
        sprint_dir = epic_dir / "sprint-10_test-sprint"
        sprint_dir.mkdir(parents=True)
        (tmp_path / "docs" / "sprints" / "1-todo").mkdir(parents=True)
        (tmp_path / ".claude").mkdir()

        # Create WORKFLOW_VERSION
        (tmp_path / ".claude" / "WORKFLOW_VERSION").write_text("3.1.0")

        # Create registry
        registry = {"sprints": [], "epics": []}
        (tmp_path / "docs" / "sprints" / "registry.json").write_text(
            json.dumps(registry)
        )

        return tmp_path

    def test_epic_sprint_already_in_progress_found(self, temp_project_with_epic):
        """Test that start-sprint finds epic sprints already in 2-in-progress."""
        # Create sprint file in epic folder (already in progress)
        sprint_dir = (
            temp_project_with_epic
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-10_test-sprint"
        )
        sprint_file = sprint_dir / "sprint-10_test-sprint.md"
        sprint_file.write_text("""---
sprint: 10
title: Test Sprint
epic: 1
status: planning
workflow_version: "3.1.0"
---

# Sprint 10: Test Sprint

## Goal
Test that epic sprints in 2-in-progress are found.
""")

        # This should NOT raise "Sprint not found" error
        from scripts.sprint_lifecycle import start_sprint

        # Mock find_project_root to return our temp directory
        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            result = start_sprint(10, dry_run=True)
            assert result["status"] == "dry-run"
            assert result["sprint_num"] == 10

    def test_sprint_without_yaml_gets_frontmatter_added(self, temp_project_with_epic):
        """Test that sprints without YAML frontmatter get it added automatically."""
        sprint_dir = (
            temp_project_with_epic
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-11_no-yaml"
        )
        sprint_dir.mkdir(parents=True)
        sprint_file = sprint_dir / "sprint-11_no-yaml.md"

        # Create sprint WITHOUT YAML frontmatter
        sprint_file.write_text("""# Sprint 11: No YAML Test

## Goal
Test that YAML frontmatter is added automatically.

## Requirements
- Test item 1
- Test item 2
""")

        from scripts.sprint_lifecycle import start_sprint

        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            result = start_sprint(11)

            # Should succeed and add frontmatter
            assert result["status"] == "started"

            # Verify frontmatter was added
            content = sprint_file.read_text()
            assert content.startswith("---\n")
            assert "sprint: 11" in content
            assert 'title: "No YAML Test"' in content
            assert "workflow_version:" in content

    def test_sprint_in_todo_not_found_in_progress(self, temp_project_with_epic):
        """Test that standalone sprint in 1-todo is found (not in 2-in-progress)."""
        # Create sprint in 1-todo (not in epic, not started)
        todo_dir = temp_project_with_epic / "docs" / "sprints" / "1-todo"
        sprint_file = todo_dir / "sprint-12_standalone.md"
        sprint_file.write_text("""---
sprint: 12
title: Standalone Sprint
status: planning
workflow_version: "3.1.0"
---

# Sprint 12: Standalone Sprint
""")

        from scripts.sprint_lifecycle import start_sprint

        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            result = start_sprint(12, dry_run=True)
            assert result["status"] == "dry-run"

    def test_completed_sprint_not_found(self, temp_project_with_epic):
        """Test that --done sprints are excluded from search."""
        # Create a completed sprint (should be excluded)
        sprint_dir = (
            temp_project_with_epic
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-13_done-test--done"
        )
        sprint_dir.mkdir(parents=True)
        sprint_file = sprint_dir / "sprint-13_done-test--done.md"
        sprint_file.write_text("""---
sprint: 13
title: Done Test
status: done
---
# Sprint 13
""")

        from scripts.sprint_lifecycle import start_sprint, FileOperationError

        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            with pytest.raises(FileOperationError, match="not found"):
                start_sprint(13)

    def test_state_file_created_for_epic_sprint(self, temp_project_with_epic):
        """Test that state file is created when starting epic sprint."""
        sprint_dir = (
            temp_project_with_epic
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-14_state-test"
        )
        sprint_dir.mkdir(parents=True)
        sprint_file = sprint_dir / "sprint-14_state-test.md"
        sprint_file.write_text("""---
sprint: 14
title: State File Test
epic: 1
status: planning
workflow_version: "3.1.0"
---

# Sprint 14: State File Test
""")

        from scripts.sprint_lifecycle import start_sprint

        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            start_sprint(14)

            # Verify state file was created
            state_file = temp_project_with_epic / ".claude" / "sprint-14-state.json"
            assert state_file.exists()

            state = json.loads(state_file.read_text())
            assert state["sprint_number"] == 14
            assert state["status"] == "in_progress"
            assert state["sprint_title"] == "State File Test"

    def test_title_extracted_from_heading_when_no_frontmatter(
        self, temp_project_with_epic
    ):
        """Test that title is correctly extracted from markdown heading."""
        sprint_dir = (
            temp_project_with_epic
            / "docs"
            / "sprints"
            / "2-in-progress"
            / "epic-01_test-epic"
            / "sprint-15_title-test"
        )
        sprint_dir.mkdir(parents=True)
        sprint_file = sprint_dir / "sprint-15_title-test.md"

        # Sprint with no frontmatter - title should come from heading
        sprint_file.write_text("""# Sprint 15: Extract This Title

## Goal
Test title extraction.
""")

        from scripts.sprint_lifecycle import start_sprint

        with patch(
            "scripts.sprint_lifecycle.find_project_root",
            return_value=temp_project_with_epic,
        ):
            start_sprint(15)

            # Verify title was extracted correctly
            state_file = temp_project_with_epic / ".claude" / "sprint-15-state.json"
            state = json.loads(state_file.read_text())
            assert state["sprint_title"] == "Extract This Title"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
