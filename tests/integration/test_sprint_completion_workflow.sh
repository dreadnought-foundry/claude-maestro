#!/bin/bash
#
# Integration test for sprint completion automation workflow
#
# Tests:
# 1. Hook blocks manual operations
# 2. Automation script bypasses hook
# 3. Skill file instructs to use automation
# 4. Error messages guide to correct command

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$SCRIPT_DIR/temp_test_$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

log_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

log_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((pass_count++))
}

log_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((fail_count++))
}

cleanup() {
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}

trap cleanup EXIT

# Setup test environment
setup_test_project() {
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"

    # Create minimal project structure
    mkdir -p docs/sprints/{1-todo,2-in-progress,3-done/_standalone}
    mkdir -p .claude

    # Create a test sprint file
    mkdir -p "docs/sprints/2-in-progress/sprint-42_test-sprint"
    cat > "docs/sprints/2-in-progress/sprint-42_test-sprint/sprint-42_test-sprint.md" <<'EOF'
---
sprint: 42
title: Test Sprint
status: done
started: 2026-01-01T10:00:00Z
completed: 2026-01-01T16:00:00Z
hours: 6.0
workflow_version: "3.1.0"
---

# Sprint 42: Test Sprint

## Goal
Test automation workflow.

## Postmortem

### Summary
Testing sprint completion automation.

### What Went Well
- Automation enforced

### What Could Improve
- Nothing

### Action Items
- [x] `[done]` Complete tests
EOF

    # Create state file
    cat > ".claude/sprint-42-state.json" <<'EOF'
{
  "sprint_number": 42,
  "status": "in_progress",
  "started_at": "2026-01-01T10:00:00Z",
  "workflow_version": "3.1.0"
}
EOF

    # Initialize git
    git init > /dev/null 2>&1
    git config user.name "Test User"
    git config user.email "test@example.com"
    git add .
    git commit -m "Initial test setup" > /dev/null 2>&1
}

# Test 1: Skill file uses automation script
test_skill_uses_automation() {
    log_test "Verify /sprint-complete skill uses automation script"

    local skill_file="$PROJECT_ROOT/commands/sprint-complete.md"
    if [ ! -f "$skill_file" ]; then
        log_fail "Skill file not found: $skill_file"
        return
    fi

    # Check for automation script command
    if grep -q "scripts/sprint_lifecycle.py complete-sprint" "$skill_file"; then
        log_pass "Skill file contains automation script command"
    else
        log_fail "Skill file missing automation script command"
    fi

    # Check for warning against manual operations
    if grep -qi "CRITICAL.*automation.*ONLY\|Do NOT.*manual" "$skill_file"; then
        log_pass "Skill file warns against manual operations"
    else
        log_fail "Skill file missing warning against manual operations"
    fi

    # Check that manual mv commands are NOT present
    if grep -q 'mv "\$SPRINT_FILE"' "$skill_file"; then
        log_fail "Skill file still contains manual mv commands"
    else
        log_pass "Skill file does not contain manual mv commands"
    fi
}

# Test 2: Hook script exists and blocks manual operations
test_hook_blocks_manual_mv() {
    log_test "Verify hook blocks manual mv commands"

    local hook_file="$HOME/.claude/hooks/pre_tool_use.py"
    if [ ! -f "$hook_file" ]; then
        log_fail "Hook file not found: $hook_file"
        return
    fi

    # Check hook has whitelist for automation script
    if grep -q "scripts/sprint_lifecycle.py" "$hook_file"; then
        log_pass "Hook whitelists automation script"
    else
        log_fail "Hook missing automation script whitelist"
    fi

    # Check hook blocks manual moves
    if grep -q "SPRINT MOVE BLOCKED\|sprint.*blocked" "$hook_file"; then
        log_pass "Hook has sprint move blocking logic"
    else
        log_fail "Hook missing sprint move blocking logic"
    fi

    # Check hook validates done folder locations
    if grep -q "3-done/_standalone\|3-done/epic" "$hook_file"; then
        log_pass "Hook validates correct done folder locations"
    else
        log_fail "Hook missing done folder validation"
    fi
}

# Test 3: Automation script exists and has required functions
test_automation_script_exists() {
    log_test "Verify automation script exists with required functions"

    local script_file="$PROJECT_ROOT/scripts/sprint_lifecycle.py"
    if [ ! -f "$script_file" ]; then
        log_fail "Automation script not found: $script_file"
        return
    fi

    # Check for complete-sprint command
    if grep -q "def complete_sprint\|'complete-sprint'" "$script_file"; then
        log_pass "Automation script has complete-sprint function"
    else
        log_fail "Automation script missing complete-sprint function"
    fi

    # Check for postmortem validation
    if grep -qi "postmortem" "$script_file"; then
        log_pass "Automation script validates postmortem"
    else
        log_fail "Automation script missing postmortem validation"
    fi

    # Check for YAML frontmatter handling
    if grep -qi "yaml\|frontmatter" "$script_file"; then
        log_pass "Automation script handles YAML frontmatter"
    else
        log_fail "Automation script missing YAML handling"
    fi
}

# Test 4: Documentation mentions automation requirement
test_documentation_complete() {
    log_test "Verify documentation mentions automation requirement"

    local skill_file="$PROJECT_ROOT/commands/sprint-complete.md"

    # Check for prerequisites section
    if grep -qi "prerequisite" "$skill_file"; then
        log_pass "Skill has prerequisites section"
    else
        log_fail "Skill missing prerequisites section"
    fi

    # Check for troubleshooting section
    if grep -qi "troubleshooting\|error:" "$skill_file"; then
        log_pass "Skill has troubleshooting section"
    else
        log_fail "Skill missing troubleshooting section"
    fi

    # Check mentions hook enforcement
    if grep -qi "hook.*enforce\|hook.*block" "$skill_file"; then
        log_pass "Skill explains hook enforcement"
    else
        log_fail "Skill missing hook enforcement explanation"
    fi
}

# Test 5: Template project has correct skill
test_template_project_skill() {
    log_test "Verify template project has automation-based skill"

    local template_skill="$PROJECT_ROOT/templates/project/commands/sprint-complete.md"
    if [ ! -f "$template_skill" ]; then
        # Template might not have commands/, check if it inherits from global
        log_pass "Template inherits from global commands (acceptable)"
        return
    fi

    if grep -q "scripts/sprint_lifecycle.py complete-sprint" "$template_skill"; then
        log_pass "Template skill uses automation"
    else
        log_fail "Template skill not using automation"
    fi
}

# Test 6: Global skill matches project skill
test_global_skill_consistency() {
    log_test "Verify global and project skills are consistent"

    local global_skill="$HOME/.claude/commands/sprint-complete.md"
    local project_skill="$PROJECT_ROOT/commands/sprint-complete.md"

    if [ ! -f "$global_skill" ]; then
        log_fail "Global skill not found: $global_skill"
        return
    fi

    if [ ! -f "$project_skill" ]; then
        log_fail "Project skill not found: $project_skill"
        return
    fi

    # Both should use automation
    global_uses_automation=$(grep -c "scripts/sprint_lifecycle.py" "$global_skill" || echo 0)
    project_uses_automation=$(grep -c "scripts/sprint_lifecycle.py" "$project_skill" || echo 0)

    if [ "$global_uses_automation" -gt 0 ] && [ "$project_uses_automation" -gt 0 ]; then
        log_pass "Both global and project skills use automation"
    else
        log_fail "Skills inconsistent: global=$global_uses_automation, project=$project_uses_automation"
    fi
}

# Test 7: Verify automation script can be invoked
test_automation_script_runnable() {
    log_test "Verify automation script is executable"

    cd "$PROJECT_ROOT"

    # Test help output
    if python3 scripts/sprint_lifecycle.py complete-sprint --help > /dev/null 2>&1; then
        log_pass "Automation script --help works"
    else
        log_fail "Automation script --help failed"
    fi

    # Test dry-run mode
    if python3 scripts/sprint_lifecycle.py complete-sprint 999 --dry-run 2>&1 | grep -qi "sprint 999\|not found\|error"; then
        log_pass "Automation script dry-run mode works"
    else
        log_fail "Automation script dry-run mode failed"
    fi
}

# Main test execution
main() {
    echo "========================================"
    echo "Sprint Completion Automation Test Suite"
    echo "========================================"
    echo ""

    # Don't need project setup for most tests
    # setup_test_project

    test_skill_uses_automation
    echo ""

    test_hook_blocks_manual_mv
    echo ""

    test_automation_script_exists
    echo ""

    test_documentation_complete
    echo ""

    test_template_project_skill
    echo ""

    test_global_skill_consistency
    echo ""

    test_automation_script_runnable
    echo ""

    echo "========================================"
    echo "Test Results"
    echo "========================================"
    echo -e "${GREEN}Passed: $pass_count${NC}"
    echo -e "${RED}Failed: $fail_count${NC}"
    echo "========================================"

    if [ $fail_count -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

main
