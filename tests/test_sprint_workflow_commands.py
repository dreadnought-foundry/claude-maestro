"""Tests for the sprint workflow command system.

These tests validate:
1. Sprint command files exist and have correct structure
2. State file naming supports multiple concurrent sprints
3. Sprint state isolation between concurrent sprints
4. Command file content references correct state file patterns
"""

import json
import os
import re
import tempfile
from pathlib import Path
from datetime import datetime

import pytest


# Path to user's global Claude commands
CLAUDE_COMMANDS_DIR = Path.home() / ".claude" / "commands"
SPRINT_STEPS_FILE = Path.home() / ".claude" / "sprint-steps.json"


class TestSprintCommandFilesExist:
    """Verify all sprint command files exist."""

    @pytest.mark.parametrize("command_name", [
        "sprint-start",
        "sprint-status",
        "sprint-next",
        "sprint-complete",
        "sprint-abort",
        "sprint-new",
    ])
    def test_command_file_exists(self, command_name):
        """Each sprint command file should exist."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        assert command_file.exists(), f"Missing command file: {command_file}"

    def test_sprint_steps_file_exists(self):
        """Sprint steps definition file should exist."""
        assert SPRINT_STEPS_FILE.exists(), f"Missing steps file: {SPRINT_STEPS_FILE}"


class TestSprintCommandFileStructure:
    """Verify command files have correct YAML frontmatter."""

    @pytest.mark.parametrize("command_name", [
        "sprint-start",
        "sprint-status",
        "sprint-next",
        "sprint-complete",
        "sprint-abort",
        "sprint-new",
    ])
    def test_command_has_frontmatter(self, command_name):
        """Each command file should have YAML frontmatter with description."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        content = command_file.read_text()

        # Check for YAML frontmatter
        assert content.startswith("---"), f"{command_name} missing YAML frontmatter"

        # Find end of frontmatter
        end_marker = content.find("---", 3)
        assert end_marker > 0, f"{command_name} frontmatter not closed"

        frontmatter = content[3:end_marker]
        assert "description:" in frontmatter, f"{command_name} missing description"

    @pytest.mark.parametrize("command_name,expected_tools", [
        ("sprint-start", ["Read", "Write", "Glob", "Task"]),
        ("sprint-status", ["Read", "Glob"]),
        ("sprint-next", ["Read", "Write", "Edit", "Bash"]),
        ("sprint-complete", ["Read", "Write", "Edit", "Bash"]),
        ("sprint-abort", ["Read", "Write", "Edit"]),
    ])
    def test_command_has_allowed_tools(self, command_name, expected_tools):
        """Each command should declare allowed-tools in frontmatter."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        content = command_file.read_text()

        # Extract frontmatter
        end_marker = content.find("---", 3)
        frontmatter = content[3:end_marker]

        assert "allowed-tools:" in frontmatter, f"{command_name} missing allowed-tools"

        # Verify expected tools are present
        for tool in expected_tools:
            assert tool in frontmatter, f"{command_name} missing tool: {tool}"


class TestMultiSprintStateFilePattern:
    """Verify commands use sprint-specific state file pattern."""

    @pytest.mark.parametrize("command_name", [
        "sprint-start",
        "sprint-status",
        "sprint-next",
        "sprint-complete",
        "sprint-abort",
    ])
    def test_command_uses_sprint_specific_state_file(self, command_name):
        """Commands should reference sprint-{N}-state.json pattern."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        content = command_file.read_text()

        # Should reference the sprint-specific state file pattern
        # Pattern: sprint-$ARGUMENTS-state.json or sprint-{N}-state.json or sprint-*-state.json
        patterns = [
            r"sprint-\$ARGUMENTS-state\.json",
            r"sprint-\{N\}-state\.json",
            r"sprint-\*-state\.json",
            r"sprint-\$sprint_number-state\.json",
        ]

        found_pattern = any(re.search(p, content) for p in patterns)
        assert found_pattern, (
            f"{command_name} should reference sprint-specific state file pattern. "
            f"Expected one of: {patterns}"
        )

    @pytest.mark.parametrize("command_name", [
        "sprint-start",
        "sprint-status",
        "sprint-next",
        "sprint-complete",
        "sprint-abort",
    ])
    def test_command_does_not_use_single_state_file(self, command_name):
        """Commands should NOT reference the old single state file pattern."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        content = command_file.read_text()

        # Should NOT reference the old single state file (without sprint number)
        # But we need to be careful - "sprint-state.json" as a standalone reference is bad
        # "sprint-{N}-state.json" or "sprint-$ARGUMENTS-state.json" is good

        # Find all occurrences of sprint-state.json
        matches = re.findall(r'[`"\']?\.claude/sprint-state\.json[`"\']?', content)

        # This pattern is the OLD single-sprint pattern we want to avoid
        assert len(matches) == 0, (
            f"{command_name} still references old single state file pattern: "
            f".claude/sprint-state.json"
        )


class TestSprintStateIsolation:
    """Test that sprint state files are properly isolated."""

    def test_create_multiple_state_files(self, tmp_path):
        """Multiple sprint state files should be independent."""
        # Simulate creating state files for sprints 34 and 35
        sprint_34_state = {
            "sprint_number": 34,
            "sprint_title": "Feature A",
            "status": "in_progress",
            "current_step": "2.1",
        }
        sprint_35_state = {
            "sprint_number": 35,
            "sprint_title": "Feature B",
            "status": "in_progress",
            "current_step": "1.3",
        }

        # Write state files
        state_34_path = tmp_path / "sprint-34-state.json"
        state_35_path = tmp_path / "sprint-35-state.json"

        state_34_path.write_text(json.dumps(sprint_34_state, indent=2))
        state_35_path.write_text(json.dumps(sprint_35_state, indent=2))

        # Read back and verify isolation
        loaded_34 = json.loads(state_34_path.read_text())
        loaded_35 = json.loads(state_35_path.read_text())

        assert loaded_34["sprint_number"] == 34
        assert loaded_35["sprint_number"] == 35
        assert loaded_34["current_step"] != loaded_35["current_step"]

    def test_state_file_naming_pattern(self):
        """Verify state file naming follows sprint-{N}-state.json pattern."""
        for sprint_num in [1, 10, 34, 100]:
            expected_name = f"sprint-{sprint_num}-state.json"
            # Verify pattern matches
            pattern = r"sprint-\d+-state\.json"
            assert re.match(pattern, expected_name), f"Bad pattern for sprint {sprint_num}"

    def test_glob_pattern_finds_all_sprints(self, tmp_path):
        """Glob pattern should find all active sprint state files."""
        # Create multiple state files
        for sprint_num in [34, 35, 36]:
            state_file = tmp_path / f"sprint-{sprint_num}-state.json"
            state_file.write_text(json.dumps({"sprint_number": sprint_num}))

        # Use glob to find all
        found_files = list(tmp_path.glob("sprint-*-state.json"))
        assert len(found_files) == 3

        # Verify each sprint is found
        found_numbers = set()
        for f in found_files:
            match = re.search(r"sprint-(\d+)-state\.json", f.name)
            assert match
            found_numbers.add(int(match.group(1)))

        assert found_numbers == {34, 35, 36}


class TestSprintStepsDefinition:
    """Test the sprint steps definition file."""

    def test_steps_file_is_valid_json(self):
        """Sprint steps file should be valid JSON."""
        content = SPRINT_STEPS_FILE.read_text()
        steps = json.loads(content)
        assert isinstance(steps, dict)

    def test_steps_file_has_required_fields(self):
        """Sprint steps file should have version, phases, and step_order."""
        content = SPRINT_STEPS_FILE.read_text()
        steps = json.loads(content)

        assert "version" in steps
        assert "phases" in steps
        assert "step_order" in steps
        assert isinstance(steps["phases"], list)
        assert isinstance(steps["step_order"], list)

    def test_all_phases_have_steps(self):
        """Each phase should have at least one step."""
        content = SPRINT_STEPS_FILE.read_text()
        steps = json.loads(content)

        for phase in steps["phases"]:
            assert "phase" in phase
            assert "name" in phase
            assert "steps" in phase
            assert len(phase["steps"]) > 0, f"Phase {phase['phase']} has no steps"

    def test_step_order_matches_phases(self):
        """step_order should include all steps from all phases."""
        content = SPRINT_STEPS_FILE.read_text()
        steps = json.loads(content)

        # Collect all step IDs from phases
        phase_steps = set()
        for phase in steps["phases"]:
            for step in phase["steps"]:
                phase_steps.add(step["step"])

        # Compare with step_order
        order_steps = set(steps["step_order"])

        assert phase_steps == order_steps, (
            f"Mismatch between phase steps and step_order. "
            f"In phases but not in order: {phase_steps - order_steps}. "
            f"In order but not in phases: {order_steps - phase_steps}"
        )


class TestSprintStateSchema:
    """Test sprint state file schema."""

    def get_expected_state_schema(self):
        """Return the expected state file schema."""
        return {
            "sprint_number": int,
            "sprint_file": str,
            "sprint_title": str,
            "status": str,  # in_progress, complete, aborted
            "current_phase": int,
            "current_step": str,
            "started_at": str,  # ISO timestamp
            "completed_at": (str, type(None)),
            "completed_steps": list,
            "blockers": list,
            "next_action": (dict, type(None)),
            "plan_output": (dict, type(None)),
            "test_results": (dict, type(None)),
            "pre_flight_checklist": dict,
        }

    @pytest.mark.skip(reason="Command files are now thin shells - state schema is in Python automation")
    def test_state_file_schema_in_start_command(self):
        """sprint-start command should create state with correct schema."""
        # NOTE: As of v3.1.0, command files are thin shells that call Python automation.
        # State schema is now defined in scripts/sprint_lifecycle.py:start_sprint()
        # See test_sprint_automation.py for tests of the actual state creation logic.
        pass

    @pytest.mark.skip(reason="Command files are now thin shells - checklist is in Python automation")
    def test_pre_flight_checklist_items(self):
        """Pre-flight checklist should have all 9 items."""
        # NOTE: As of v3.1.0, command files are thin shells that call Python automation.
        # Pre-flight checklist is now in scripts/sprint_lifecycle.py:complete_sprint()
        # See test_sprint_automation.py for tests of the completion logic.
        pass


class TestConcurrentSprintScenarios:
    """Test realistic concurrent sprint scenarios."""

    def test_two_sprints_different_phases(self, tmp_path):
        """Two sprints can be at different phases simultaneously."""
        sprint_34 = {
            "sprint_number": 34,
            "sprint_title": "API Enhancement",
            "status": "in_progress",
            "current_phase": 2,
            "current_step": "2.2",
            "started_at": "2025-12-01T10:00:00Z",
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-01T10:05:00Z"},
                {"step": "1.2", "completed_at": "2025-12-01T10:15:00Z"},
                {"step": "2.1", "completed_at": "2025-12-01T10:30:00Z"},
            ],
        }

        sprint_35 = {
            "sprint_number": 35,
            "sprint_title": "UI Improvements",
            "status": "in_progress",
            "current_phase": 1,
            "current_step": "1.2",
            "started_at": "2025-12-01T11:00:00Z",
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-01T11:05:00Z"},
            ],
        }

        # Write both state files
        (tmp_path / "sprint-34-state.json").write_text(json.dumps(sprint_34, indent=2))
        (tmp_path / "sprint-35-state.json").write_text(json.dumps(sprint_35, indent=2))

        # Load and verify independence
        loaded_34 = json.loads((tmp_path / "sprint-34-state.json").read_text())
        loaded_35 = json.loads((tmp_path / "sprint-35-state.json").read_text())

        # Sprints should be at different phases
        assert loaded_34["current_phase"] == 2
        assert loaded_35["current_phase"] == 1

        # Different number of completed steps
        assert len(loaded_34["completed_steps"]) == 3
        assert len(loaded_35["completed_steps"]) == 1

    def test_one_sprint_complete_one_in_progress(self, tmp_path):
        """One completed sprint shouldn't affect in-progress sprint."""
        sprint_34 = {
            "sprint_number": 34,
            "status": "complete",
            "completed_at": "2025-12-01T15:00:00Z",
        }

        sprint_35 = {
            "sprint_number": 35,
            "status": "in_progress",
            "completed_at": None,
        }

        (tmp_path / "sprint-34-state.json").write_text(json.dumps(sprint_34, indent=2))
        (tmp_path / "sprint-35-state.json").write_text(json.dumps(sprint_35, indent=2))

        loaded_34 = json.loads((tmp_path / "sprint-34-state.json").read_text())
        loaded_35 = json.loads((tmp_path / "sprint-35-state.json").read_text())

        assert loaded_34["status"] == "complete"
        assert loaded_35["status"] == "in_progress"

    def test_three_concurrent_sprints(self, tmp_path):
        """System should support three or more concurrent sprints."""
        sprints = [
            {"sprint_number": 34, "status": "in_progress", "current_step": "2.1"},
            {"sprint_number": 35, "status": "in_progress", "current_step": "3.2"},
            {"sprint_number": 36, "status": "in_progress", "current_step": "1.1"},
        ]

        for sprint in sprints:
            path = tmp_path / f"sprint-{sprint['sprint_number']}-state.json"
            path.write_text(json.dumps(sprint, indent=2))

        # Find all state files
        found = list(tmp_path.glob("sprint-*-state.json"))
        assert len(found) == 3

        # Each should have unique state
        steps = set()
        for f in found:
            data = json.loads(f.read_text())
            steps.add(data["current_step"])

        assert len(steps) == 3, "All three sprints should be at different steps"


class TestCommandDocumentation:
    """Test that commands have proper usage documentation."""

    @pytest.mark.parametrize("command_name", [
        "sprint-start",
        "sprint-status",
        "sprint-next",
        "sprint-complete",
        "sprint-abort",
    ])
    def test_command_documents_multi_sprint_support(self, command_name):
        """Each command should document multi-sprint support."""
        command_file = CLAUDE_COMMANDS_DIR / f"{command_name}.md"
        content = command_file.read_text()

        # Should mention concurrent/multiple sprints through various indicators
        multi_sprint_indicators = [
            "multiple concurrent sprints",
            "sprint-specific state file",
            "sprint number",
            "sprint-$ARGUMENTS-state",  # Dynamic sprint state files
            "sprint-*-state",  # Glob pattern for multiple sprints
            "$ARGUMENTS",  # Indicates sprint number is parameterized
        ]

        found = any(indicator.lower() in content.lower() for indicator in multi_sprint_indicators)
        assert found, f"{command_name} should document multi-sprint support"

    def test_sprint_status_supports_all_argument(self):
        """sprint-status should support 'all' argument to list all sprints."""
        command_file = CLAUDE_COMMANDS_DIR / "sprint-status.md"
        content = command_file.read_text()

        assert "all" in content.lower(), "sprint-status should support 'all' argument"
