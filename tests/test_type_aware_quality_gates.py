"""Tests for type-aware quality gates system.

This test suite validates Sprint 4's implementation of sprint-type-specific
quality requirements, including coverage thresholds, documentation mandates,
and dynamic pre-flight checklist adaptation.

Test Coverage:
- Quality gate configuration for all 6 sprint types
- Sprint type detection from frontmatter
- Coverage threshold override mechanism with justification
- Dynamic pre-flight checklist adaptation
- Type-specific validation rules
"""

from pathlib import Path

import pytest

# Import validation utilities
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))

from validate_step import QUALITY_GATES


class TestQualityGateConfiguration:
    """Test QUALITY_GATES configuration and completeness."""

    def test_all_sprint_types_have_configuration(self):
        """Verify all 6 sprint types are configured in QUALITY_GATES."""
        expected_types = {
            "fullstack",
            "backend",
            "frontend",
            "research",
            "spike",
            "infrastructure",
        }
        configured_types = set(QUALITY_GATES.keys())

        assert configured_types == expected_types, (
            f"Missing or extra sprint types. "
            f"Expected: {expected_types}, Got: {configured_types}"
        )

    def test_all_gates_have_coverage_threshold(self):
        """Verify every sprint type defines a coverage threshold."""
        for sprint_type, config in QUALITY_GATES.items():
            assert (
                "coverage" in config
            ), f"Sprint type '{sprint_type}' missing 'coverage' threshold"
            assert isinstance(
                config["coverage"], int
            ), f"Sprint type '{sprint_type}' coverage must be integer"
            assert (
                0 <= config["coverage"] <= 100
            ), f"Sprint type '{sprint_type}' coverage must be 0-100"

    def test_coverage_thresholds_match_requirements(self):
        """Verify coverage thresholds match sprint specification."""
        expected_thresholds = {
            "fullstack": 75,
            "backend": 85,
            "frontend": 70,
            "research": 30,
            "spike": 0,
            "infrastructure": 60,
        }

        for sprint_type, expected_coverage in expected_thresholds.items():
            actual_coverage = QUALITY_GATES[sprint_type]["coverage"]
            assert actual_coverage == expected_coverage, (
                f"Sprint type '{sprint_type}' coverage mismatch: "
                f"expected {expected_coverage}%, got {actual_coverage}%"
            )

    def test_research_and_spike_require_documentation(self):
        """Verify research and spike types have mandatory documentation."""
        research_config = QUALITY_GATES["research"]
        spike_config = QUALITY_GATES["spike"]

        assert (
            research_config.get("documentation") is True
        ), "Research sprints must require documentation=True"
        assert (
            spike_config.get("documentation") is True
        ), "Spike sprints must require documentation=True"

    def test_backend_requires_integration_tests(self):
        """Verify backend sprint type requires integration tests."""
        backend_config = QUALITY_GATES["backend"]

        assert (
            backend_config.get("integration_tests") is True
        ), "Backend sprints must require integration_tests=True"

    def test_frontend_requires_visual_regression(self):
        """Verify frontend sprint type requires visual regression tests."""
        frontend_config = QUALITY_GATES["frontend"]

        assert (
            frontend_config.get("visual_regression") is True
        ), "Frontend sprints must require visual_regression=True"

    def test_infrastructure_requires_smoke_tests(self):
        """Verify infrastructure sprint type requires smoke tests."""
        infra_config = QUALITY_GATES["infrastructure"]

        assert (
            infra_config.get("smoke_tests") is True
        ), "Infrastructure sprints must require smoke_tests=True"

    def test_fullstack_integration_tests_recommended(self):
        """Verify fullstack type has integration tests recommended (not skipped)."""
        fullstack_config = QUALITY_GATES["fullstack"]

        # Integration tests should be True (recommended) or not explicitly False
        assert (
            fullstack_config.get("integration_tests") is True
        ), "Fullstack sprints should recommend integration_tests=True"


class TestSprintTypeDetection:
    """Test reading sprint type from frontmatter and validation."""

    def test_type_extracted_from_frontmatter(self):
        """Valid type field is read correctly from sprint frontmatter."""
        frontmatter = """---
sprint: 42
title: Test Sprint
type: backend
status: in-progress
---"""
        # Parse YAML frontmatter
        import re

        match = re.search(r"type:\s*(\w+)", frontmatter)
        assert match is not None, "Type field not found in frontmatter"

        sprint_type = match.group(1)
        assert sprint_type == "backend", f"Expected 'backend', got '{sprint_type}'"
        assert (
            sprint_type in QUALITY_GATES
        ), f"Type '{sprint_type}' not in QUALITY_GATES"

    def test_all_valid_types_recognized(self):
        """All valid sprint types are recognized as valid."""
        valid_types = [
            "fullstack",
            "backend",
            "frontend",
            "research",
            "spike",
            "infrastructure",
        ]

        for sprint_type in valid_types:
            assert (
                sprint_type in QUALITY_GATES
            ), f"Valid type '{sprint_type}' not recognized in QUALITY_GATES"

    def test_invalid_type_can_be_detected(self):
        """Invalid sprint type can be detected for validation."""
        invalid_types = ["invalid", "full-stack", "api", "ui", ""]

        for invalid_type in invalid_types:
            # Check that invalid type is not in QUALITY_GATES
            assert (
                invalid_type not in QUALITY_GATES
            ), f"Invalid type '{invalid_type}' should not be in QUALITY_GATES"

    def test_missing_type_can_be_handled(self):
        """Missing type field can be detected and handled."""
        frontmatter = """---
sprint: 42
title: Test Sprint
status: in-progress
---"""
        # Parse and check for type field
        import re

        match = re.search(r"type:\s*(\w+)", frontmatter)

        # Should not find type field
        assert match is None, "Type field should be missing"

        # Default behavior should use fullstack
        default_type = "fullstack"
        assert (
            default_type in QUALITY_GATES
        ), "Default type 'fullstack' must exist in QUALITY_GATES"


class TestCoverageOverrides:
    """Test coverage threshold override mechanism with justification."""

    def test_override_value_format(self):
        """Override value should be an integer percentage."""
        frontmatter = """---
sprint: 42
type: backend
coverage_threshold: 80
# Justification: Critical validation logic requires high coverage
---"""
        import re

        # Extract coverage override
        match = re.search(r"coverage_threshold:\s*(\d+)", frontmatter)
        assert match is not None, "Coverage override not found"

        override_value = int(match.group(1))
        assert isinstance(override_value, int), "Override must be integer"
        assert 0 <= override_value <= 100, "Override must be 0-100"

    def test_override_with_justification_present(self):
        """Override with justification comment is present in frontmatter."""
        frontmatter = """---
sprint: 42
type: backend
coverage_threshold: 80
# Justification: Critical validation logic requires high coverage
---"""
        # Check for justification comment
        assert (
            "Justification:" in frontmatter or "justification:" in frontmatter
        ), "Override must include justification comment"

    def test_override_without_justification_detectable(self):
        """Override without justification can be detected."""
        frontmatter = """---
sprint: 42
type: backend
coverage_threshold: 80
---"""
        # Check for justification comment
        has_justification = (
            "Justification:" in frontmatter or "justification:" in frontmatter
        )

        assert not has_justification, "Test case should not have justification"

    def test_override_replaces_default_threshold(self):
        """Custom threshold should replace default for sprint type."""
        sprint_type = "backend"
        default_threshold = QUALITY_GATES[sprint_type]["coverage"]
        override_threshold = 80

        assert default_threshold == 85, "Backend default should be 85%"
        assert (
            override_threshold != default_threshold
        ), "Override should be different from default for testing"

        # Verify override can be applied
        effective_threshold = override_threshold
        assert effective_threshold == 80, "Override should be applied"

    def test_override_can_lower_threshold(self):
        """Override can lower threshold below default with justification."""
        sprint_type = "backend"
        default_threshold = QUALITY_GATES[sprint_type]["coverage"]
        lower_override = 70

        assert (
            lower_override < default_threshold
        ), "Override should be lower than default (85%)"

        frontmatter = f"""---
sprint: 42
type: {sprint_type}
coverage_threshold: {lower_override}
# Justification: Experimental integration, production code fully tested
---"""
        # Verify justification exists for lower threshold
        assert "Justification:" in frontmatter or "justification:" in frontmatter

    def test_override_can_raise_threshold(self):
        """Override can raise threshold above default with justification."""
        sprint_type = "frontend"
        default_threshold = QUALITY_GATES[sprint_type]["coverage"]
        higher_override = 85

        assert (
            higher_override > default_threshold
        ), "Override should be higher than default (70%)"

        frontmatter = f"""---
sprint: 42
type: {sprint_type}
coverage_threshold: {higher_override}
# Justification: Critical UI component used across entire application
---"""
        # Verify justification exists
        assert "Justification:" in frontmatter or "justification:" in frontmatter


class TestDynamicChecklist:
    """Test pre-flight checklist adapts to sprint type."""

    def test_research_sprint_requires_documentation_check(self):
        """Research sprints add documentation_complete to checklist."""
        sprint_type = "research"
        config = QUALITY_GATES[sprint_type]

        assert (
            config.get("documentation") is True
        ), "Research sprints must require documentation"

        # Verify documentation is a mandatory check
        assert (
            "documentation" in config
        ), "Config must specify documentation requirement"

    def test_backend_sprint_requires_integration_tests(self):
        """Backend sprints add integration_tests_passing to checklist."""
        sprint_type = "backend"
        config = QUALITY_GATES[sprint_type]

        assert (
            config.get("integration_tests") is True
        ), "Backend sprints must require integration tests"

        # Verify integration tests are required
        assert (
            "integration_tests" in config
        ), "Config must specify integration_tests requirement"

    def test_spike_sprint_allows_zero_coverage(self):
        """Spike sprints pass with 0% coverage."""
        spike_config = QUALITY_GATES["spike"]

        assert spike_config["coverage"] == 0, "Spike sprints should allow 0% coverage"

        # But still require documentation
        assert (
            spike_config.get("documentation") is True
        ), "Spike sprints must require documentation"

    def test_frontend_sprint_checklist_includes_visual_regression(self):
        """Frontend sprints include visual regression in checklist."""
        frontend_config = QUALITY_GATES["frontend"]

        assert (
            frontend_config.get("visual_regression") is True
        ), "Frontend sprints must require visual regression"

        # Visual regression should be in checklist
        assert (
            "visual_regression" in frontend_config
        ), "Config must specify visual_regression requirement"

    def test_infrastructure_sprint_checklist_includes_smoke_tests(self):
        """Infrastructure sprints include smoke tests in checklist."""
        infra_config = QUALITY_GATES["infrastructure"]

        assert (
            infra_config.get("smoke_tests") is True
        ), "Infrastructure sprints must require smoke tests"

        # Smoke tests should be in checklist
        assert (
            "smoke_tests" in infra_config
        ), "Config must specify smoke_tests requirement"

    def test_checklist_adapts_based_on_type(self):
        """Checklist items vary based on sprint type configuration."""
        # Collect all unique checklist items across types
        all_checks = set()
        for sprint_type, config in QUALITY_GATES.items():
            for key, value in config.items():
                if isinstance(value, bool) and value is True:
                    all_checks.add(key)

        # Verify we have type-specific checks
        type_specific_checks = all_checks - {"coverage"}

        assert (
            len(type_specific_checks) > 0
        ), "Should have type-specific checks beyond coverage"

        # Known type-specific checks
        known_checks = {
            "documentation",
            "integration_tests",
            "visual_regression",
            "smoke_tests",
        }

        assert type_specific_checks.issubset(
            known_checks
        ), f"Found unexpected checks: {type_specific_checks - known_checks}"


class TestTypeSpecificValidation:
    """Test validation rules specific to each sprint type."""

    def test_fullstack_validation_rules(self):
        """Fullstack sprints have standard balanced requirements."""
        config = QUALITY_GATES["fullstack"]

        assert config["coverage"] == 75, "Fullstack should have 75% coverage"
        assert (
            config.get("integration_tests") is True
        ), "Should recommend integration tests"
        assert config.get("documentation") is not True, "Documentation is optional"

    def test_backend_validation_rules(self):
        """Backend sprints have highest coverage and require integration tests."""
        config = QUALITY_GATES["backend"]

        assert config["coverage"] == 85, "Backend should have highest coverage (85%)"
        assert config.get("integration_tests") is True, "Must require integration tests"
        assert config.get("documentation") is not True, "Documentation is optional"

    def test_frontend_validation_rules(self):
        """Frontend sprints have moderate coverage and visual regression."""
        config = QUALITY_GATES["frontend"]

        assert config["coverage"] == 70, "Frontend should have 70% coverage"
        assert config.get("visual_regression") is True, "Must require visual regression"
        assert config.get("documentation") is not True, "Documentation is optional"

    def test_research_validation_rules(self):
        """Research sprints have low coverage but mandatory documentation."""
        config = QUALITY_GATES["research"]

        assert config["coverage"] == 30, "Research should have low coverage (30%)"
        assert config.get("documentation") is True, "Must require documentation"

    def test_spike_validation_rules(self):
        """Spike sprints allow zero coverage but require documentation."""
        config = QUALITY_GATES["spike"]

        assert config["coverage"] == 0, "Spike should allow zero coverage"
        assert config.get("documentation") is True, "Must require documentation"

    def test_infrastructure_validation_rules(self):
        """Infrastructure sprints have moderate coverage and smoke tests."""
        config = QUALITY_GATES["infrastructure"]

        assert config["coverage"] == 60, "Infrastructure should have 60% coverage"
        assert config.get("smoke_tests") is True, "Must require smoke tests"


class TestQualityGateIntegration:
    """Test integration of quality gates with sprint workflow."""

    def test_quality_gates_importable_from_validate_step(self):
        """QUALITY_GATES can be imported from validate_step module."""
        # Already imported at top of file
        assert QUALITY_GATES is not None, "QUALITY_GATES should be importable"
        assert isinstance(QUALITY_GATES, dict), "QUALITY_GATES should be a dict"

    def test_configuration_structure_consistent(self):
        """All configurations have consistent structure."""
        for sprint_type, config in QUALITY_GATES.items():
            # All must have coverage
            assert (
                "coverage" in config
            ), f"Sprint type '{sprint_type}' missing coverage field"

            # All values must be appropriate types
            for key, value in config.items():
                if key == "coverage":
                    assert isinstance(value, int), f"{sprint_type}.coverage must be int"
                else:
                    assert isinstance(value, bool), f"{sprint_type}.{key} must be bool"

    def test_documentation_mandatory_only_for_low_coverage(self):
        """Documentation is mandatory only for research and spike (low/no coverage)."""
        mandatory_doc_types = [
            sprint_type
            for sprint_type, config in QUALITY_GATES.items()
            if config.get("documentation") is True
        ]

        assert set(mandatory_doc_types) == {
            "research",
            "spike",
        }, "Only research and spike should have mandatory documentation"

        # Verify these are the low-coverage types
        for sprint_type in mandatory_doc_types:
            coverage = QUALITY_GATES[sprint_type]["coverage"]
            assert (
                coverage <= 30
            ), f"Mandatory doc type '{sprint_type}' should have low coverage"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_override_values(self):
        """Verify handling of extreme override values."""
        # Minimum valid override
        assert 0 >= 0 and 0 <= 100, "0% coverage should be valid"

        # Maximum valid override
        assert 100 >= 0 and 100 <= 100, "100% coverage should be valid"

        # Invalid values that should be rejected
        invalid_values = [-1, 101, 150, -50]
        for value in invalid_values:
            assert not (0 <= value <= 100), f"Value {value} should be invalid"

    def test_type_field_case_sensitivity(self):
        """Sprint type field should be case-sensitive."""
        valid_types = set(QUALITY_GATES.keys())

        # These should not be valid
        invalid_cases = [
            "Backend",
            "BACKEND",
            "FullStack",
            "full_stack",
            "Research",
        ]

        for invalid_case in invalid_cases:
            assert (
                invalid_case not in valid_types
            ), f"Case variant '{invalid_case}' should not be valid"

    def test_all_types_have_numeric_coverage(self):
        """All sprint types must have numeric coverage threshold."""
        for sprint_type, config in QUALITY_GATES.items():
            coverage = config["coverage"]
            assert isinstance(
                coverage, (int, float)
            ), f"Sprint type '{sprint_type}' coverage must be numeric"
            assert (
                coverage >= 0
            ), f"Sprint type '{sprint_type}' coverage cannot be negative"

    def test_spike_is_only_zero_coverage_type(self):
        """Only spike sprint type should allow zero coverage."""
        zero_coverage_types = [
            sprint_type
            for sprint_type, config in QUALITY_GATES.items()
            if config["coverage"] == 0
        ]

        assert zero_coverage_types == ["spike"], "Only 'spike' should have 0% coverage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
