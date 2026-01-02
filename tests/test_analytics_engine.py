"""Tests for analytics_engine.py analytics computation utilities.

These tests validate:
1. Phase timing calculation from completed_steps
2. Historical comparison against sprint type averages
3. Bottleneck identification with recommendations
4. ASCII bar chart rendering for phase breakdown
5. Coverage delta tracking (before/after/delta)
6. Agent execution tracking with timing and token estimation
7. Analytics report generation for completed and in-progress sprints
8. Edge cases: empty data, missing fields, single step, time gaps

Following TDD: These tests are written BEFORE implementation.
All tests should FAIL initially until analytics_engine.py is created.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from analytics_engine.py (will fail until implemented)
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from analytics_engine import (
        calculate_phase_timings,
        calculate_historical_comparison,
        identify_bottlenecks,
        render_phase_breakdown,
        track_coverage_delta,
        track_agent_execution,
        generate_analytics_report,
        estimate_tokens_from_output,
        AnalyticsError,
    )
except ImportError:
    # Allow import to fail during TDD phase
    pass


@pytest.fixture
def sample_completed_steps():
    """Sample completed_steps data with realistic timestamps."""
    base_time = datetime(2025, 12, 30, 10, 0, 0)
    return [
        {
            "step": "1.1",
            "completed_at": (base_time + timedelta(minutes=15)).isoformat(),
        },
        {
            "step": "1.2",
            "completed_at": (base_time + timedelta(minutes=30)).isoformat(),
        },
        {
            "step": "1.3",
            "completed_at": (base_time + timedelta(minutes=45)).isoformat(),
        },
        {
            "step": "2.1",
            "completed_at": (base_time + timedelta(minutes=75)).isoformat(),
        },
        {
            "step": "2.2",
            "completed_at": (base_time + timedelta(minutes=135)).isoformat(),
        },
        {
            "step": "3.1",
            "completed_at": (base_time + timedelta(minutes=165)).isoformat(),
        },
        {
            "step": "3.2",
            "completed_at": (base_time + timedelta(minutes=180)).isoformat(),
        },
    ]


@pytest.fixture
def sample_agent_executions():
    """Sample agent execution data."""
    return [
        {
            "agent": "Plan",
            "phase": "1.2",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_at": "2025-12-30T10:15:00Z",
            "output_length": 4800,  # chars
        },
        {
            "agent": "product-engineer",
            "phase": "2.1",
            "started_at": "2025-12-30T10:45:00Z",
            "completed_at": "2025-12-30T11:45:00Z",
            "output_length": 12000,
        },
        {
            "agent": "quality-engineer",
            "phase": "3.1",
            "started_at": "2025-12-30T12:00:00Z",
            "completed_at": "2025-12-30T12:30:00Z",
            "output_length": 6000,
        },
    ]


@pytest.fixture
def sample_historical_data():
    """Sample historical sprint data for comparison."""
    return {
        "sprints": {
            "1": {
                "type": "fullstack",
                "duration_hours": 2.5,
                "phase_breakdown": {
                    "planning": 0.5,
                    "implementation": 1.2,
                    "validation": 0.6,
                    "documentation": 0.2,
                },
                "coverage_improvement": 4.5,
            },
            "2": {
                "type": "fullstack",
                "duration_hours": 3.0,
                "phase_breakdown": {
                    "planning": 0.6,
                    "implementation": 1.5,
                    "validation": 0.7,
                    "documentation": 0.2,
                },
                "coverage_improvement": 3.8,
            },
            "3": {
                "type": "backend",
                "duration_hours": 2.0,
                "phase_breakdown": {
                    "planning": 0.3,
                    "implementation": 1.2,
                    "validation": 0.4,
                    "documentation": 0.1,
                },
                "coverage_improvement": 6.2,
            },
        }
    }


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create project structure
        (project_root / ".claude").mkdir()
        (project_root / "docs" / "sprints").mkdir(parents=True)

        # Create sample registry
        registry = {
            "version": "1.0",
            "sprints": {
                "1": {
                    "type": "fullstack",
                    "duration_hours": 2.5,
                    "phase_breakdown": {
                        "planning": 0.5,
                        "implementation": 1.2,
                        "validation": 0.6,
                        "documentation": 0.2,
                    },
                    "coverage_improvement": 4.5,
                },
                "2": {
                    "type": "fullstack",
                    "duration_hours": 3.0,
                    "phase_breakdown": {
                        "planning": 0.6,
                        "implementation": 1.5,
                        "validation": 0.7,
                        "documentation": 0.2,
                    },
                    "coverage_improvement": 3.8,
                },
            },
        }
        registry_path = project_root / "docs" / "sprints" / "registry.json"
        registry_path.write_text(json.dumps(registry, indent=2))

        # Create sample state file
        state = {
            "sprint_number": 5,
            "current_step": "3.1",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_steps": [],
            "agent_executions": [],
        }
        state_path = project_root / ".claude" / "sprint-state.json"
        state_path.write_text(json.dumps(state, indent=2))

        yield project_root


class TestCalculatePhaseTimings:
    """Test phase timing calculation from completed_steps."""

    def test_calculates_timings_for_all_phases(self, sample_completed_steps):
        """Should calculate time spent in each workflow phase."""
        result = calculate_phase_timings(sample_completed_steps)

        assert "planning" in result
        assert "implementation" in result
        assert "validation" in result

        # Phase 1 (planning): steps 1.1-1.3 = 45 minutes
        assert result["planning"] == pytest.approx(0.75, abs=0.01)  # hours

        # Phase 2 (implementation): steps 2.1-2.2 = 60 minutes
        assert result["implementation"] == pytest.approx(1.0, abs=0.01)

        # Phase 3 (validation): steps 3.1-3.2 = 15 minutes
        assert result["validation"] == pytest.approx(0.25, abs=0.01)

    def test_maps_step_prefixes_to_phases(self, sample_completed_steps):
        """Should correctly map step prefixes (1.x, 2.x, etc.) to phase names."""
        result = calculate_phase_timings(sample_completed_steps)

        # Verify all expected phases are present
        assert set(result.keys()) == {"planning", "implementation", "validation"}

    def test_handles_empty_steps(self):
        """Should handle empty completed_steps gracefully."""
        result = calculate_phase_timings([])

        assert result == {}

    def test_handles_single_step(self):
        """Should handle single step without errors."""
        steps = [{"step": "1.1", "completed_at": "2025-12-30T10:00:00Z"}]

        result = calculate_phase_timings(steps)

        # Single step means no duration can be calculated
        assert result == {} or result["planning"] == 0

    def test_handles_gaps_in_time(self):
        """Should handle time gaps between phases correctly."""
        steps = [
            {"step": "1.1", "completed_at": "2025-12-30T10:00:00Z"},
            {"step": "1.2", "completed_at": "2025-12-30T10:30:00Z"},
            # Gap of 2 hours
            {"step": "2.1", "completed_at": "2025-12-30T12:30:00Z"},
            {"step": "2.2", "completed_at": "2025-12-30T13:00:00Z"},
        ]

        result = calculate_phase_timings(steps)

        # Should calculate based on actual timestamps
        assert result["planning"] == pytest.approx(0.5, abs=0.01)
        assert result["implementation"] == pytest.approx(0.5, abs=0.01)

    def test_handles_out_of_order_steps(self):
        """Should handle steps not in chronological order."""
        steps = [
            {"step": "1.2", "completed_at": "2025-12-30T10:30:00Z"},
            {"step": "1.1", "completed_at": "2025-12-30T10:00:00Z"},
            {"step": "2.1", "completed_at": "2025-12-30T11:00:00Z"},
        ]

        result = calculate_phase_timings(steps)

        # Should sort by timestamp first
        assert result["planning"] == pytest.approx(0.5, abs=0.01)
        assert result["implementation"] >= 0

    def test_handles_invalid_timestamps(self):
        """Should raise error for invalid timestamp formats."""
        steps = [
            {"step": "1.1", "completed_at": "invalid-timestamp"},
            {"step": "1.2", "completed_at": "2025-12-30T10:30:00Z"},
        ]

        with pytest.raises(AnalyticsError, match="Invalid timestamp"):
            calculate_phase_timings(steps)

    def test_includes_all_workflow_phases(self):
        """Should support all workflow phases including documentation and commit."""
        steps = [
            {"step": "1.1", "completed_at": "2025-12-30T10:00:00Z"},
            {"step": "2.1", "completed_at": "2025-12-30T10:30:00Z"},
            {"step": "3.1", "completed_at": "2025-12-30T11:00:00Z"},
            {"step": "4.1", "completed_at": "2025-12-30T11:15:00Z"},  # documentation
            {"step": "5.1", "completed_at": "2025-12-30T11:20:00Z"},  # commit
        ]

        result = calculate_phase_timings(steps)

        assert "planning" in result
        assert "implementation" in result
        assert "validation" in result
        assert "documentation" in result
        assert "commit" in result


class TestCalculateHistoricalComparison:
    """Test historical comparison against sprint type averages."""

    def test_compares_to_same_sprint_type(self, sample_historical_data):
        """Should compare current sprint to historical averages of same type."""
        current_metrics = {
            "type": "fullstack",
            "duration_hours": 2.0,
            "coverage_improvement": 5.0,
            "phase_breakdown": {
                "planning": 0.4,
                "implementation": 1.0,
                "validation": 0.5,
                "documentation": 0.1,
            },
        }

        result = calculate_historical_comparison(
            current_metrics, sample_historical_data
        )

        assert "avg_duration" in result
        assert result["avg_duration"] == 2.75  # Average of 2.5 and 3.0
        assert "avg_coverage_improvement" in result
        assert result["avg_coverage_improvement"] == pytest.approx(4.15, abs=0.01)

    def test_calculates_percentile_rank(self, sample_historical_data):
        """Should calculate percentile rank for current sprint."""
        current_metrics = {
            "type": "fullstack",
            "duration_hours": 2.0,  # Faster than both historical sprints
            "coverage_improvement": 5.0,
        }

        result = calculate_historical_comparison(
            current_metrics, sample_historical_data
        )

        assert "duration_percentile" in result
        assert result["duration_percentile"] == 100  # Faster than all

    def test_handles_no_historical_data_for_type(self, sample_historical_data):
        """Should handle case when no historical data exists for sprint type."""
        current_metrics = {
            "type": "spike",  # No historical spike sprints
            "duration_hours": 1.5,
            "coverage_improvement": 0,
        }

        result = calculate_historical_comparison(
            current_metrics, sample_historical_data
        )

        assert result["avg_duration"] is None
        assert result["message"] == "No historical data for sprint type: spike"

    def test_excludes_current_sprint_from_comparison(self, sample_historical_data):
        """Should exclude current sprint from historical averages."""
        current_metrics = {
            "type": "fullstack",
            "duration_hours": 2.5,
            "sprint_number": 1,  # Same as one in historical data
        }

        result = calculate_historical_comparison(
            current_metrics, sample_historical_data
        )

        # Should only use sprint 2 for average
        assert result["avg_duration"] == 3.0

    def test_compares_phase_percentages(self, sample_historical_data):
        """Should compare phase percentage breakdown to historical averages."""
        current_metrics = {
            "type": "fullstack",
            "duration_hours": 2.0,
            "phase_breakdown": {
                "planning": 0.4,
                "implementation": 1.0,
                "validation": 0.5,
                "documentation": 0.1,
            },
        }

        result = calculate_historical_comparison(
            current_metrics, sample_historical_data
        )

        assert "avg_phase_percentages" in result
        # Planning avg: (0.5 + 0.6) / 2 = 0.55
        # Total avg: 2.75 hours
        # Planning %: 0.55 / 2.75 = 20%
        assert result["avg_phase_percentages"]["planning"] == pytest.approx(20, abs=1)

    def test_handles_empty_historical_data(self):
        """Should handle empty historical data gracefully."""
        current_metrics = {"type": "fullstack", "duration_hours": 2.0}
        historical_data = {"sprints": {}}

        result = calculate_historical_comparison(current_metrics, historical_data)

        assert result["avg_duration"] is None
        assert "No historical data" in result["message"]


class TestIdentifyBottlenecks:
    """Test bottleneck identification with recommendations."""

    def test_flags_phases_exceeding_threshold(self, sample_historical_data):
        """Should flag phases exceeding 1.5x historical percentage."""
        current_metrics = {
            "type": "fullstack",
            "phase_breakdown": {
                "planning": 0.5,
                "implementation": 2.0,  # Much longer than historical
                "validation": 0.3,
                "documentation": 0.1,
            },
        }

        result = identify_bottlenecks(current_metrics, sample_historical_data)

        assert len(result["bottlenecks"]) > 0
        assert any(b["phase"] == "implementation" for b in result["bottlenecks"])

    def test_generates_actionable_recommendations(self, sample_historical_data):
        """Should generate actionable recommendations for bottlenecks."""
        current_metrics = {
            "type": "fullstack",
            "phase_breakdown": {
                "planning": 0.5,
                "implementation": 2.5,
                "validation": 0.3,
                "documentation": 0.1,
            },
        }

        result = identify_bottlenecks(current_metrics, sample_historical_data)

        bottleneck = next(
            b for b in result["bottlenecks"] if b["phase"] == "implementation"
        )
        assert "recommendation" in bottleneck
        assert len(bottleneck["recommendation"]) > 0
        # Should suggest breaking into smaller tasks or parallel execution
        assert (
            "smaller" in bottleneck["recommendation"].lower()
            or "parallel" in bottleneck["recommendation"].lower()
        )

    def test_no_bottlenecks_when_within_threshold(self, sample_historical_data):
        """Should return no bottlenecks when all phases within threshold."""
        current_metrics = {
            "type": "fullstack",
            "phase_breakdown": {
                "planning": 0.5,
                "implementation": 1.2,
                "validation": 0.6,
                "documentation": 0.2,
            },
        }

        result = identify_bottlenecks(current_metrics, sample_historical_data)

        assert len(result["bottlenecks"]) == 0

    def test_handles_missing_phase_in_historical_data(self, sample_historical_data):
        """Should handle phases not present in historical data."""
        current_metrics = {
            "type": "fullstack",
            "phase_breakdown": {
                "planning": 0.5,
                "implementation": 1.2,
                "new_phase": 2.0,  # Not in historical data
            },
        }

        result = identify_bottlenecks(current_metrics, sample_historical_data)

        # Should not crash, may or may not flag as bottleneck
        assert isinstance(result, dict)
        assert "bottlenecks" in result

    def test_calculates_percentage_over_threshold(self, sample_historical_data):
        """Should calculate how much phase exceeds threshold."""
        current_metrics = {
            "type": "fullstack",
            "phase_breakdown": {
                "planning": 0.5,
                "implementation": 3.0,  # Way over threshold
                "validation": 0.3,
            },
        }

        result = identify_bottlenecks(current_metrics, sample_historical_data)

        bottleneck = next(
            b for b in result["bottlenecks"] if b["phase"] == "implementation"
        )
        assert "percentage_over" in bottleneck
        assert bottleneck["percentage_over"] > 50  # Significantly over


class TestRenderPhaseBreakdown:
    """Test ASCII bar chart rendering for phase breakdown."""

    def test_generates_ascii_bar_chart(self):
        """Should generate ASCII bar charts for phase breakdown."""
        phase_timings = {
            "planning": 0.25,
            "implementation": 1.0,
            "validation": 0.35,
            "documentation": 0.15,
        }

        result = render_phase_breakdown(phase_timings)

        assert isinstance(result, str)
        # Should contain phase names
        assert "Planning" in result or "planning" in result
        assert "Implementation" in result or "implementation" in result
        # Should contain visual bars
        assert "█" in result or "[" in result
        # Should contain percentages
        assert "%" in result
        # Should contain hours
        assert "h)" in result

    def test_formats_as_expected(self):
        """Should format output as: Phase [██░░░░░░░░] XX% (X.XXh)."""
        phase_timings = {
            "planning": 0.25,
            "implementation": 1.0,
        }

        result = render_phase_breakdown(phase_timings)

        # Check format matches expected pattern
        assert "[" in result
        assert "]" in result
        assert "%" in result
        assert "(" in result and "h)" in result

    def test_bar_length_proportional_to_percentage(self):
        """Should render bar length proportional to phase percentage."""
        phase_timings = {
            "phase_a": 1.0,  # 50%
            "phase_b": 1.0,  # 50%
        }

        result = render_phase_breakdown(phase_timings)

        # Both phases should have similar bar lengths
        lines = result.split("\n")
        assert len(lines) >= 2

    def test_handles_zero_duration_phases(self):
        """Should handle phases with zero duration."""
        phase_timings = {
            "planning": 0.5,
            "implementation": 0,
            "validation": 0.5,
        }

        result = render_phase_breakdown(phase_timings)

        assert "implementation" in result.lower() or "Implementation" in result
        # Should show 0% or empty bar
        assert "0%" in result or "░░░░░░░░░░" in result

    def test_handles_empty_phase_timings(self):
        """Should handle empty phase timings gracefully."""
        result = render_phase_breakdown({})

        assert result == "" or "No phase data" in result

    def test_aligns_output_columns(self):
        """Should align phase names, bars, and percentages in columns."""
        phase_timings = {
            "planning": 0.25,
            "implementation": 1.0,
            "validation": 0.35,
        }

        result = render_phase_breakdown(phase_timings)

        lines = result.strip().split("\n")
        # All lines should have similar structure and alignment
        assert len(lines) == 3
        for line in lines:
            assert "[" in line
            assert "]" in line


class TestTrackCoverageDelta:
    """Test coverage delta tracking (before/after/delta)."""

    def test_calculates_coverage_delta(self):
        """Should calculate before/after/delta coverage."""
        result = track_coverage_delta(before=73.2, after=78.5)

        assert result["before"] == 73.2
        assert result["after"] == 78.5
        assert result["delta"] == pytest.approx(5.3, abs=0.01)

    def test_handles_negative_delta(self):
        """Should handle negative delta (coverage decreased)."""
        result = track_coverage_delta(before=80.0, after=75.5)

        assert result["delta"] == pytest.approx(-4.5, abs=0.01)

    def test_handles_zero_delta(self):
        """Should handle zero delta (no change)."""
        result = track_coverage_delta(before=75.0, after=75.0)

        assert result["delta"] == 0.0

    def test_validates_coverage_range(self):
        """Should validate coverage is between 0 and 100."""
        with pytest.raises(AnalyticsError, match="Coverage must be between 0 and 100"):
            track_coverage_delta(before=-5, after=80)

        with pytest.raises(AnalyticsError, match="Coverage must be between 0 and 100"):
            track_coverage_delta(before=75, after=105)

    def test_handles_none_values(self):
        """Should handle None values for incomplete sprints."""
        result = track_coverage_delta(before=75.0, after=None)

        assert result["before"] == 75.0
        assert result["after"] is None
        assert result["delta"] is None


class TestTrackAgentExecution:
    """Test agent execution tracking with timing and token estimation."""

    def test_records_agent_execution_with_timing(self):
        """Should record agent start/complete with timing."""
        execution = track_agent_execution(
            agent="product-engineer",
            phase="2.1",
            started_at="2025-12-30T10:00:00Z",
            completed_at="2025-12-30T11:00:00Z",
            output_length=10000,
        )

        assert execution["agent"] == "product-engineer"
        assert execution["phase"] == "2.1"
        assert execution["started_at"] == "2025-12-30T10:00:00Z"
        assert execution["completed_at"] == "2025-12-30T11:00:00Z"
        assert execution["duration_seconds"] == 3600

    def test_estimates_tokens_from_output_length(self):
        """Should estimate tokens from output length (chars / 4)."""
        execution = track_agent_execution(
            agent="Plan",
            phase="1.1",
            started_at="2025-12-30T10:00:00Z",
            completed_at="2025-12-30T10:15:00Z",
            output_length=4800,  # chars
        )

        # 4800 chars / 4 = 1200 tokens
        assert execution["estimated_tokens"] == 1200

    def test_tracks_files_modified(self):
        """Should track files modified via git diff."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="file1.py\nfile2.py\nfile3.py\n", returncode=0
            )

            execution = track_agent_execution(
                agent="product-engineer",
                phase="2.1",
                started_at="2025-12-30T10:00:00Z",
                completed_at="2025-12-30T11:00:00Z",
                output_length=10000,
            )

            assert execution["files_modified"] == 3

    def test_handles_git_diff_failure(self):
        """Should handle git diff failure gracefully."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("git not available")

            execution = track_agent_execution(
                agent="product-engineer",
                phase="2.1",
                started_at="2025-12-30T10:00:00Z",
                completed_at="2025-12-30T11:00:00Z",
                output_length=10000,
            )

            assert (
                execution["files_modified"] == 0 or execution["files_modified"] is None
            )


class TestEstimateTokensFromOutput:
    """Test token estimation from output length."""

    def test_estimates_tokens_using_char_division(self):
        """Should estimate tokens as chars / 4."""
        tokens = estimate_tokens_from_output(4800)
        assert tokens == 1200

        tokens = estimate_tokens_from_output(10000)
        assert tokens == 2500

    def test_handles_zero_length(self):
        """Should handle zero length output."""
        tokens = estimate_tokens_from_output(0)
        assert tokens == 0

    def test_rounds_to_integer(self):
        """Should round to nearest integer."""
        tokens = estimate_tokens_from_output(4801)
        assert isinstance(tokens, int)
        assert tokens == 1200  # 4801 / 4 = 1200.25 -> 1200


class TestGenerateAnalyticsReport:
    """Test analytics report generation from sprint state."""

    def test_generates_complete_report_for_completed_sprint(self, temp_project):
        """Should generate complete analytics report for completed sprint."""
        # Create completed sprint state
        state = {
            "sprint_number": 5,
            "current_step": "6.4",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_at": "2025-12-30T13:00:00Z",
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-30T10:30:00Z"},
                {"step": "2.1", "completed_at": "2025-12-30T11:30:00Z"},
                {"step": "3.1", "completed_at": "2025-12-30T12:30:00Z"},
            ],
            "agent_executions": [
                {
                    "agent": "Plan",
                    "phase": "1.1",
                    "started_at": "2025-12-30T10:00:00Z",
                    "completed_at": "2025-12-30T10:30:00Z",
                    "output_length": 4800,
                }
            ],
            "coverage_delta": {"before": 73.2, "after": 78.5, "delta": 5.3},
        }

        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.write_text(json.dumps(state, indent=2))

        report = generate_analytics_report(temp_project, sprint_number=5)

        assert "sprint_number" in report
        assert report["sprint_number"] == 5
        assert "duration_hours" in report
        assert "phase_breakdown" in report
        assert "agent_executions" in report
        assert "coverage_delta" in report
        assert "comparison" in report

    def test_supports_in_progress_sprints(self, temp_project):
        """Should generate report for in-progress sprints."""
        state = {
            "sprint_number": 5,
            "current_step": "2.1",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_at": None,  # Still in progress
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-30T10:30:00Z"},
            ],
        }

        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.write_text(json.dumps(state, indent=2))

        report = generate_analytics_report(temp_project, sprint_number=5)

        assert report["status"] == "in-progress"
        assert report["completed_at"] is None
        assert "duration_hours" in report  # Should calculate elapsed time

    def test_includes_phase_breakdown_visualization(self, temp_project):
        """Should include ASCII visualization of phase breakdown."""
        state = {
            "sprint_number": 5,
            "current_step": "3.1",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-30T10:30:00Z"},
                {"step": "2.1", "completed_at": "2025-12-30T11:30:00Z"},
            ],
        }

        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.write_text(json.dumps(state, indent=2))

        report = generate_analytics_report(temp_project, sprint_number=5)

        assert "visualization" in report
        assert isinstance(report["visualization"], str)
        assert "█" in report["visualization"] or "[" in report["visualization"]

    def test_includes_historical_comparison(self, temp_project):
        """Should include comparison to historical averages."""
        report = generate_analytics_report(temp_project, sprint_number=5)

        assert "comparison" in report
        assert isinstance(report["comparison"], dict)

    def test_includes_bottleneck_identification(self, temp_project):
        """Should identify and report bottlenecks."""
        state = {
            "sprint_number": 5,
            "current_step": "3.1",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_steps": [
                {"step": "1.1", "completed_at": "2025-12-30T10:15:00Z"},
                {"step": "2.1", "completed_at": "2025-12-30T10:30:00Z"},
                {"step": "2.2", "completed_at": "2025-12-30T13:00:00Z"},  # Very long
            ],
        }

        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.write_text(json.dumps(state, indent=2))

        report = generate_analytics_report(temp_project, sprint_number=5)

        assert "bottlenecks" in report
        assert isinstance(report["bottlenecks"], list)

    def test_handles_missing_state_file(self, temp_project):
        """Should raise error when state file doesn't exist."""
        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.unlink()  # Delete state file

        with pytest.raises(AnalyticsError, match="State file not found"):
            generate_analytics_report(temp_project, sprint_number=5)

    def test_handles_malformed_state_file(self, temp_project):
        """Should raise error for malformed JSON."""
        state_path = temp_project / ".claude" / "sprint-state.json"
        state_path.write_text("{ invalid json }")

        with pytest.raises(AnalyticsError, match="Invalid state file"):
            generate_analytics_report(temp_project, sprint_number=5)


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_handles_missing_fields_gracefully(self):
        """Should handle missing optional fields in state."""
        state = {
            "sprint_number": 5,
            "current_step": "2.1",
            # Missing: agent_executions, coverage_delta, etc.
        }

        # Should not crash, return partial data
        phase_timings = calculate_phase_timings(state.get("completed_steps", []))
        assert isinstance(phase_timings, dict)

    def test_handles_very_large_state_files(self, temp_project):
        """Should handle state files approaching size limit (100KB)."""
        # Create large state with many agent executions
        large_state = {
            "sprint_number": 5,
            "current_step": "3.1",
            "started_at": "2025-12-30T10:00:00Z",
            "completed_steps": [
                {"step": f"{i}.1", "completed_at": "2025-12-30T10:00:00Z"}
                for i in range(1, 100)
            ],
            "agent_executions": [
                {
                    "agent": f"agent-{i}",
                    "phase": "2.1",
                    "started_at": "2025-12-30T10:00:00Z",
                    "completed_at": "2025-12-30T11:00:00Z",
                    "output_length": 10000,
                }
                for i in range(100)
            ],
        }

        state_path = temp_project / ".claude" / "sprint-state.json"
        state_json = json.dumps(large_state, indent=2)
        state_path.write_text(state_json)

        # Should complete within time limit
        import time

        start = time.time()
        report = generate_analytics_report(temp_project, sprint_number=5)
        elapsed = time.time() - start

        assert elapsed < 2.0  # Must complete in < 2 seconds
        assert isinstance(report, dict)

    def test_handles_timezone_differences(self):
        """Should handle timestamps with different timezone formats."""
        steps = [
            {"step": "1.1", "completed_at": "2025-12-30T10:00:00Z"},  # UTC
            {
                "step": "1.2",
                "completed_at": "2025-12-30T10:30:00+00:00",
            },  # UTC with offset
            {"step": "2.1", "completed_at": "2025-12-30T05:00:00-05:00"},  # EST
        ]

        result = calculate_phase_timings(steps)

        # Should handle all formats correctly
        assert isinstance(result, dict)
        assert "planning" in result

    def test_performance_with_many_historical_sprints(self, temp_project):
        """Should perform well with large historical dataset."""
        # Create registry with 100 sprints
        large_registry = {
            "version": "1.0",
            "sprints": {
                str(i): {
                    "type": "fullstack",
                    "duration_hours": 2.0 + (i * 0.1),
                    "phase_breakdown": {
                        "planning": 0.5,
                        "implementation": 1.0,
                        "validation": 0.4,
                        "documentation": 0.1,
                    },
                    "coverage_improvement": 4.0 + (i * 0.1),
                }
                for i in range(1, 101)
            },
        }

        registry_path = temp_project / "docs" / "sprints" / "registry.json"
        registry_path.write_text(json.dumps(large_registry, indent=2))

        current_metrics = {
            "type": "fullstack",
            "duration_hours": 2.5,
            "sprint_number": 200,
        }

        # Should complete quickly even with 100 historical sprints
        import time

        start = time.time()
        result = calculate_historical_comparison(current_metrics, large_registry)
        elapsed = time.time() - start

        assert elapsed < 0.5  # Should be very fast
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
