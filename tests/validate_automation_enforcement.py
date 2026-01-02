#!/usr/bin/env python3
"""
Quick validation that sprint completion automation is enforced.

This script validates that the automation-only approach is properly configured:
1. Skill files use automation script
2. Hook blocks manual operations
3. Automation script exists and is callable
"""

import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    passed = 0
    failed = 0

    print("=" * 60)
    print("Sprint Completion Automation Validation")
    print("=" * 60)
    print()

    # Test 1: Skill uses automation
    print("TEST 1: Skill file uses automation script")
    skill_file = project_root / "commands" / "sprint-complete.md"
    if skill_file.exists():
        content = skill_file.read_text()
        if "scripts/sprint_lifecycle.py complete-sprint" in content:
            print("✓ PASS: Skill uses automation script")
            passed += 1
        else:
            print("✗ FAIL: Skill doesn't use automation script")
            failed += 1

        if "CRITICAL" in content and ("Do NOT" in content or "ONLY" in content):
            print("✓ PASS: Skill warns against manual operations")
            passed += 1
        else:
            print("✗ FAIL: Skill missing warning")
            failed += 1
    else:
        print(f"✗ FAIL: Skill file not found: {skill_file}")
        failed += 2
    print()

    # Test 2: Global skill also uses automation
    print("TEST 2: Global skill consistency")
    global_skill = Path.home() / ".claude" / "commands" / "sprint-complete.md"
    if global_skill.exists():
        content = global_skill.read_text()
        if "scripts/sprint_lifecycle.py" in content:
            print("✓ PASS: Global skill uses automation")
            passed += 1
        else:
            print("✗ FAIL: Global skill doesn't use automation")
            failed += 1
    else:
        print("⚠ SKIP: Global skill not found (acceptable)")
    print()

    # Test 3: Hook exists with proper enforcement
    print("TEST 3: Hook enforcement")
    hook_file = Path.home() / ".claude" / "hooks" / "pre_tool_use.py"
    if hook_file.exists():
        content = hook_file.read_text()
        if "scripts/sprint_lifecycle.py" in content:
            print("✓ PASS: Hook whitelists automation script")
            passed += 1
        else:
            print("✗ FAIL: Hook missing automation whitelist")
            failed += 1

        if "SPRINT MOVE BLOCKED" in content or "BLOCKED" in content:
            print("✓ PASS: Hook blocks sprint moves")
            passed += 1
        else:
            print("✗ FAIL: Hook missing blocking logic")
            failed += 1
    else:
        print(f"✗ FAIL: Hook not found: {hook_file}")
        failed += 2
    print()

    # Test 4: Automation script callable
    print("TEST 4: Automation script")
    result = subprocess.run(
        [sys.executable, "scripts/sprint_lifecycle.py", "complete-sprint", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ PASS: Automation script is callable")
        passed += 1
    else:
        print(f"✗ FAIL: Automation script error: {result.stderr}")
        failed += 1
    print()

    # Test 5: Requirements.txt exists with pytest
    print("TEST 5: Test dependencies")
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text()
        if "pytest" in content:
            print("✓ PASS: pytest in requirements.txt")
            passed += 1
        else:
            print("✗ FAIL: pytest missing from requirements.txt")
            failed += 1
    else:
        print("✗ FAIL: requirements.txt not found")
        failed += 1
    print()

    # Summary
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("✓ All validation checks passed!")
        return 0
    else:
        print(f"✗ {failed} checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
