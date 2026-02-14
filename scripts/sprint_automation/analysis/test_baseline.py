"""
Test baseline snapshot and comparison.

Captures test suite state before a sprint starts so you can diff
pre-existing failures from new ones introduced by the sprint.

Usage:
    python -m sprint_automation.analysis.test_baseline capture <sprint_num>
    python -m sprint_automation.analysis.test_baseline compare <sprint_num>
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.file_ops import find_project_root


def _get_baseline_path(project_root: Path, sprint_num: int) -> Path:
    return project_root / ".claude" / f"test-baseline-{sprint_num}.json"


def _run_tests(project_root: Path) -> dict:
    """Run test suite, return {total, passed, failed, skipped, failing_tests}."""
    result = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "failing_tests": []}

    try:
        proc = subprocess.run(
            ["npx", "vitest", "run", "--reporter=json"],
            cwd=str(project_root),
            capture_output=True, text=True, timeout=300,
        )
        output = proc.stdout or proc.stderr
        data = json.loads(output)
        result["total"] = data.get("numTotalTests", 0)
        result["passed"] = data.get("numPassedTests", 0)
        result["failed"] = data.get("numFailedTests", 0)
        result["skipped"] = data.get("numPendingTests", 0)
        for suite in data.get("testResults", []):
            for test in suite.get("assertionResults", suite.get("testResults", [])):
                if test.get("status") == "failed":
                    result["failing_tests"].append(test.get("fullName", "unknown"))
    except json.JSONDecodeError:
        # Fallback: parse summary line from text output
        output = (proc.stdout or "") + (proc.stderr or "")
        for pattern, key in [
            (r"(\d+)\s+passed", "passed"), (r"(\d+)\s+failed", "failed"),
            (r"(\d+)\s+skipped", "skipped"),
        ]:
            m = re.search(pattern, output)
            if m:
                result[key] = int(m.group(1))
        result["total"] = result["passed"] + result["failed"] + result["skipped"]
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        result["error"] = str(e)

    return result


def capture_baseline(sprint_num: int, project_root: Optional[Path] = None) -> dict:
    """Capture test suite state before sprint work begins."""
    if project_root is None:
        project_root = find_project_root()

    print(f"Capturing test baseline for Sprint {sprint_num}...")
    test_state = _run_tests(project_root)

    baseline = {
        "sprint_num": sprint_num,
        "captured_at": datetime.now().isoformat(),
        **test_state,
    }

    path = _get_baseline_path(project_root, sprint_num)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2))

    print(f"  Total: {baseline['total']}  Passed: {baseline['passed']}  Failed: {baseline['failed']}")
    if baseline["failing_tests"]:
        print(f"  Pre-existing failures: {len(baseline['failing_tests'])}")
    return baseline


def compare_baseline(sprint_num: int, project_root: Optional[Path] = None) -> dict:
    """Compare current test state against the pre-sprint baseline."""
    if project_root is None:
        project_root = find_project_root()

    baseline_path = _get_baseline_path(project_root, sprint_num)
    if not baseline_path.exists():
        print(f"No baseline found for sprint {sprint_num}")
        return {"error": f"No baseline for sprint {sprint_num}", "new_failures": []}

    baseline = json.loads(baseline_path.read_text())
    current = _run_tests(project_root)

    old_fails = set(baseline.get("failing_tests", []))
    new_fails = set(current.get("failing_tests", []))

    comparison = {
        "baseline_total": baseline.get("total", 0),
        "current_total": current.get("total", 0),
        "new_failures": sorted(new_fails - old_fails),
        "pre_existing_failures": sorted(new_fails & old_fails),
        "fixed_tests": sorted(old_fails - new_fails),
    }

    print(f"\nTest Baseline Comparison (Sprint {sprint_num}):")
    print(f"  Baseline: {comparison['baseline_total']} tests, {len(old_fails)} failing")
    print(f"  Current:  {comparison['current_total']} tests, {len(new_fails)} failing")
    print(f"  New failures: {len(comparison['new_failures'])}  Pre-existing: {len(comparison['pre_existing_failures'])}  Fixed: {len(comparison['fixed_tests'])}")

    if comparison["new_failures"]:
        print("\n  NEW failures (introduced by this sprint):")
        for t in comparison["new_failures"]:
            print(f"    - {t}")

    return comparison


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test baseline snapshot and comparison")
    parser.add_argument("action", choices=["capture", "compare"])
    parser.add_argument("sprint_num", type=int)
    parser.add_argument("--project-root", type=str, default=None)
    args = parser.parse_args()

    root = Path(args.project_root).resolve() if args.project_root else None

    if args.action == "capture":
        capture_baseline(args.sprint_num, project_root=root)
    else:
        r = compare_baseline(args.sprint_num, project_root=root)
        if r.get("new_failures"):
            sys.exit(1)
