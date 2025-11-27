#!/bin/bash
# Automated test runner for Note Book
# Runs all tests and reports results

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$SCRIPT_DIR"
RESULTS_FILE="$PROJECT_ROOT/Nov 6th-1/TASKS_COMPLETED.md"

echo "========================================================================"
echo "NOTE BOOK TEST SUITE"
echo "========================================================================"
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Tests directory: $TESTS_DIR"
echo ""

# Track overall status
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test and record result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "------------------------------------------------------------------------"
    echo "Running: $test_name"
    echo "Command: $test_command"
    echo "------------------------------------------------------------------------"
    
    if eval "$test_command"; then
        echo "✓ PASSED: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAILED: $test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Create a nested X session using Xnest (user-space, no root needed)
export NESTED_DISPLAY=:99
Xnest $NESTED_DISPLAY -ac -geometry 1024x768 &
XNEST_PID=$!
sleep 2  # Wait for Xnest to start

# Function to clean up Xnest
function cleanup_xnest {
    kill $XNEST_PID || true
}
trap cleanup_xnest EXIT

# Store original display
ORIG_DISPLAY=$DISPLAY
export DISPLAY=$NESTED_DISPLAY

echo "========================================================================"
echo "TEST 1: Installation Process"
echo "========================================================================"
run_test "Installation test" "python3 '$TESTS_DIR/test_installer.py'"

echo "========================================================================"
echo "TEST 2: Icon Contrast Ratios"
echo "========================================================================"
run_test "Icon contrast test" "python3 '$TESTS_DIR/test_icon_contrast.py'"

echo ""
echo "========================================================================"
echo "TEST SUITE COMPLETE"
echo "========================================================================"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    
    # Append to TASKS_COMPLETED.md
    {
        echo ""
        echo "## ✅ Test run completed: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo ""
        echo "**Command**: \`./tests/run_tests.sh\`"
        echo ""
        echo "**Results**:"
        echo "- Tests passed: $TESTS_PASSED"
        echo "- Tests failed: $TESTS_FAILED"
        echo "- Exit code: 0"
        echo ""
        echo "All icon contrast tests passed. Ready to proceed with implementation."
        echo ""
    } >> "$RESULTS_FILE"
    
    exit 0
else
    echo "✗ $TESTS_FAILED test(s) failed"
    
    # Append to TASKS_COMPLETED.md
    {
        echo ""
        echo "## ⚠️ Test run failed: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo ""
        echo "**Command**: \`./tests/run_tests.sh\`"
        echo ""
        echo "**Results**:"
        echo "- Tests passed: $TESTS_PASSED"
        echo "- Tests failed: $TESTS_FAILED"
        echo "- Exit code: 1"
        echo ""
        echo "Icon contrast tests identified issues. Review output above."
        echo ""
    } >> "$RESULTS_FILE"
    
    exit 1
fi
