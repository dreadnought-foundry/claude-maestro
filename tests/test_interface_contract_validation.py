"""
Test suite for interface contract validation.

Tests:
- Valid contracts pass validation
- Enum case mismatches caught
- Type mismatches detected
- Missing required fields fail
- Phase 1.5 gate enforcement
- Fullstack vs backend-only handling
- Nested type validation
- Performance requirements (< 5s)
"""

import json
import tempfile
import time
from pathlib import Path

from scripts.validate_interface_contract import (
    InterfaceContractValidator,
    find_contract_for_sprint,
)


class TestContractValidation:
    """Test core contract validation functionality."""

    def test_valid_contract_passes(self):
        """Should pass validation for a valid fullstack contract."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "queries": {"userFeatures": "returns: [Feature!]!"},
                    "types": {
                        "Feature": {
                            "key": "String!",
                            "name": "String!",
                            "enabled": "Boolean!",
                        }
                    },
                    "enums": {"FeatureStatus": ["ENABLED", "DISABLED", "BETA"]},
                },
                "frontend_interface": {
                    "hooks": ["useFeatures"],
                    "types": ["Feature", "FeatureStatus"],
                },
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is True
            assert len(errors) == 0

    def test_enum_case_mismatch_caught(self):
        """Should catch enum values that are not UPPERCASE."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "enums": {
                        "FeatureStatus": [
                            "enabled",
                            "DISABLED",
                            "Beta",
                        ]  # lowercase + mixed case
                    }
                },
                "frontend_interface": {"types": ["FeatureStatus"]},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert len(errors) >= 2
            assert any("enabled" in err and "UPPERCASE" in err for err in errors)
            assert any("Beta" in err and "UPPERCASE" in err for err in errors)

    def test_type_mismatch_detected(self):
        """Should detect when frontend types don't match backend."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {"types": {"Feature": {"key": "String!"}}},
                "frontend_interface": {
                    "types": ["Feature", "NonExistentType", "AnotherMissingType"]
                },
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert len(errors) >= 2
            assert any(
                "NonExistentType" in err and "not defined" in err for err in errors
            )
            assert any("AnotherMissingType" in err for err in errors)

    def test_missing_required_fields_fail(self):
        """Should fail validation when required fields are missing."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                # Missing backend_interface and frontend_interface
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert len(errors) > 0
            # Either jsonschema validation error or manual validation error
            assert any(
                "Schema validation failed" in err or
                "missing" in err.lower() or
                "required" in err.lower()
                for err in errors
            )

    def test_backend_only_sprint_skips_validation(self):
        """Should skip contract validation for non-fullstack sprints."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "backend-only",
                "backend_interface": {},
                "frontend_interface": {},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            # Should pass because validation is skipped for backend-only
            assert is_valid is True
            assert len(errors) == 0

    def test_nested_type_validation(self):
        """Should validate nested type definitions correctly."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "types": {
                        "Feature": {
                            "key": "String!",
                            "metadata": {
                                "type": "[MetadataField!]",
                                "fields": {"key": "String!", "value": "String!"},
                            },
                        },
                        "MetadataField": {"key": "String!", "value": "String!"},
                    }
                },
                "frontend_interface": {"types": ["Feature", "MetadataField"]},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is True
            assert len(errors) == 0

    def test_nested_type_undefined_reference(self):
        """Should catch undefined types in nested definitions."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "types": {
                        "Feature": {
                            "metadata": {
                                "type": "[UndefinedType!]",  # Not defined anywhere
                                "fields": {},
                            }
                        }
                    }
                },
                "frontend_interface": {"types": ["Feature"]},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert any("UndefinedType" in err and "undefined" in err for err in errors)

    def test_query_return_type_validation(self):
        """Should validate query return types are defined."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "queries": {
                        "getFeature": "returns: UndefinedType!"  # Type not defined
                    }
                },
                "frontend_interface": {},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert any("UndefinedType" in err and "undefined" in err for err in errors)

    def test_hook_naming_convention(self):
        """Should enforce React hook naming conventions."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {},
                "frontend_interface": {
                    "hooks": [
                        "getFeatures",
                        "useFeatures",
                        "fetchData",
                    ]  # Invalid: should start with 'use'
                },
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert any(
                "getFeatures" in err and "must start with 'use'" in err
                for err in errors
            )
            assert any(
                "fetchData" in err and "must start with 'use'" in err for err in errors
            )

    def test_validation_performance(self):
        """Should validate contract in < 5 seconds."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"

            # Create a large contract with many types
            types = {}
            for i in range(100):
                types[f"Type{i}"] = {f"field{j}": "String!" for j in range(20)}

            contract = {
                "sprint": 1,
                "type": "fullstack",
                "backend_interface": {
                    "types": types,
                    "enums": {
                        f"Enum{i}": [f"VALUE_{j}" for j in range(10)] for i in range(50)
                    },
                },
                "frontend_interface": {"types": [f"Type{i}" for i in range(100)]},
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            start_time = time.time()
            is_valid, errors = validator.validate(contract_path)
            elapsed = time.time() - start_time

            # Should complete in < 5 seconds
            assert elapsed < 5.0, f"Validation took {elapsed:.2f}s, should be < 5s"
            assert is_valid is True

    def test_invalid_json_file(self):
        """Should handle invalid JSON gracefully."""
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.json"
            with open(contract_path, "w") as f:
                f.write("{ invalid json }")

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is False
            assert len(errors) == 1
            assert "Invalid JSON" in errors[0]

    def test_file_not_found(self):
        """Should handle missing contract files gracefully."""
        validator = InterfaceContractValidator()

        is_valid, errors = validator.validate(Path("/nonexistent/contract.json"))

        assert is_valid is False
        assert len(errors) == 1
        assert "not found" in errors[0]


class TestContractDiscovery:
    """Test contract file discovery for sprints."""

    def test_find_contract_in_sprint_folder(self):
        """Should find contract in sprint folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sprint folder structure
            sprint_dir = Path(tmpdir) / "docs/sprints/2-in-progress/sprint-03_test"
            sprint_dir.mkdir(parents=True)

            contract_path = sprint_dir / "contract-sprint-3.json"
            contract_path.write_text("{}")

            # Change to tmpdir to simulate project root
            import os

            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                found_path = find_contract_for_sprint(3)
                assert found_path is not None
                assert found_path.name == "contract-sprint-3.json"
            finally:
                os.chdir(original_dir)

    def test_find_contract_in_claude_dir(self):
        """Should find contract in .claude directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()

            contract_path = claude_dir / "sprint-5-contract.json"
            contract_path.write_text("{}")

            import os

            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                found_path = find_contract_for_sprint(5)
                assert found_path is not None
                assert found_path.name == "sprint-5-contract.json"
            finally:
                os.chdir(original_dir)

    def test_contract_not_found_returns_none(self):
        """Should return None when contract not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                found_path = find_contract_for_sprint(999)
                assert found_path is None
            finally:
                os.chdir(original_dir)


class TestIntegration:
    """Integration tests for workflow scenarios."""

    def test_fullstack_sprint_workflow(self):
        """Should enforce contract validation for fullstack sprint."""
        # This would be tested via workflow integration
        # For now, verify the components work together
        validator = InterfaceContractValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "sprint-10-contract.json"
            contract = {
                "sprint": 10,
                "type": "fullstack",
                "backend_interface": {
                    "queries": {"getUsers": "returns: [User!]!"},
                    "types": {"User": {"id": "ID!", "name": "String!"}},
                    "enums": {"UserRole": ["ADMIN", "USER"]},
                },
                "frontend_interface": {
                    "hooks": ["useUsers"],
                    "types": ["User", "UserRole"],
                },
            }

            with open(contract_path, "w") as f:
                json.dump(contract, f)

            is_valid, errors = validator.validate(contract_path)

            assert is_valid is True
            assert len(errors) == 0
