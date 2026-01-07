#!/usr/bin/env python3
"""
Comparison test for sprint_lifecycle v1 vs v2.

Verifies that the modular package (v2) has API parity with the original (v1).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_api_parity():
    """Verify both versions export the same public API."""
    print("Testing API parity between v1 and v2...\n")

    # Import v1 (original)
    import scripts.sprint_lifecycle as v1

    # Import v2 (modular facade)
    import scripts.sprint_lifecycle_v2 as v2

    # List of public functions to check
    public_functions = [
        # Core sprint operations
        "create_sprint",
        "start_sprint",
        "complete_sprint",
        "abort_sprint",
        "block_sprint",
        "resume_sprint",
        "get_sprint_status",
        "advance_step",
        "generate_postmortem",
        "move_to_done",
        "recover_sprint",
        # Epic operations
        "create_epic",
        "start_epic",
        "complete_epic",
        "archive_epic",
        "reset_epic",
        "get_epic_status",
        "list_epics",
        "add_to_epic",
        # Registry operations
        "get_next_sprint_number",
        "get_next_epic_number",
        "register_new_sprint",
        "register_new_epic",
        "update_registry",
        "check_epic_completion",
        # Utility functions
        "find_project_root",
        "check_git_clean",
        "create_git_tag",
        # Project operations
        "create_project",
    ]

    # Exception classes
    exception_classes = [
        "SprintLifecycleError",
        "GitError",
        "FileOperationError",
        "ValidationError",
    ]

    # Check functions
    missing_in_v1 = []
    missing_in_v2 = []
    matched = []

    for func_name in public_functions:
        has_v1 = hasattr(v1, func_name)
        has_v2 = hasattr(v2, func_name)

        if has_v1 and has_v2:
            matched.append(func_name)
        elif not has_v1:
            missing_in_v1.append(func_name)
        elif not has_v2:
            missing_in_v2.append(func_name)

    # Check exception classes
    for cls_name in exception_classes:
        has_v1 = hasattr(v1, cls_name)
        has_v2 = hasattr(v2, cls_name)

        if has_v1 and has_v2:
            matched.append(cls_name)
        elif not has_v1:
            missing_in_v1.append(cls_name)
        elif not has_v2:
            missing_in_v2.append(cls_name)

    # Report results
    print(f"✓ Matched: {len(matched)} items")
    for item in matched:
        print(f"    {item}")

    if missing_in_v1:
        print(f"\n⚠ Missing in v1 (new in v2): {len(missing_in_v1)} items")
        for item in missing_in_v1:
            print(f"    {item}")

    if missing_in_v2:
        print(f"\n✗ Missing in v2: {len(missing_in_v2)} items")
        for item in missing_in_v2:
            print(f"    {item}")
        return False

    print(f"\n{'='*50}")
    print("✓ API PARITY VERIFIED")
    print(f"{'='*50}")
    return True


def test_function_signatures():
    """Verify function signatures match between v1 and v2."""
    print("\nTesting function signatures...\n")

    import inspect
    import scripts.sprint_lifecycle as v1
    import scripts.sprint_lifecycle_v2 as v2

    functions_to_check = [
        "create_sprint",
        "start_sprint",
        "complete_sprint",
        "abort_sprint",
        "create_epic",
    ]

    mismatches = []

    for func_name in functions_to_check:
        v1_func = getattr(v1, func_name, None)
        v2_func = getattr(v2, func_name, None)

        if v1_func and v2_func:
            v1_sig = inspect.signature(v1_func)
            v2_sig = inspect.signature(v2_func)

            if str(v1_sig) == str(v2_sig):
                print(f"  ✓ {func_name}{v1_sig}")
            else:
                print(f"  ✗ {func_name}")
                print(f"      v1: {v1_sig}")
                print(f"      v2: {v2_sig}")
                mismatches.append(func_name)

    if mismatches:
        print(f"\n✗ Signature mismatches: {len(mismatches)}")
        return False

    print(f"\n{'='*50}")
    print("✓ SIGNATURES MATCH")
    print(f"{'='*50}")
    return True


def test_utility_functions():
    """Test that utility functions return same results."""
    print("\nTesting utility functions...\n")

    import scripts.sprint_lifecycle as v1
    import scripts.sprint_lifecycle_v2 as v2

    # Test find_project_root
    v1_root = v1.find_project_root()
    v2_root = v2.find_project_root()

    if v1_root == v2_root:
        print(f"  ✓ find_project_root() → {v1_root}")
    else:
        print("  ✗ find_project_root() mismatch:")
        print(f"      v1: {v1_root}")
        print(f"      v2: {v2_root}")
        return False

    # Test check_git_clean (just check it runs, don't compare results as git state may change)
    try:
        v1.check_git_clean()
        v2.check_git_clean()
        print("  ✓ check_git_clean() runs without error")
    except Exception as e:
        print(f"  ✗ check_git_clean() error: {e}")
        return False

    print(f"\n{'='*50}")
    print("✓ UTILITY FUNCTIONS WORK")
    print(f"{'='*50}")
    return True


def main():
    """Run all comparison tests."""
    print("=" * 60)
    print("SPRINT LIFECYCLE V1 vs V2 COMPARISON")
    print("=" * 60)

    results = []

    results.append(("API Parity", test_api_parity()))
    results.append(("Signatures", test_function_signatures()))
    results.append(("Utilities", test_utility_functions()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ ALL COMPARISON TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
