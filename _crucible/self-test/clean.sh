#!/bin/bash

# Self-test script for _crucible/clean.py
# Tests that clean.py properly removes checkout.yaml and repository directories

# Note: Don't use set -e since we test different scenarios

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLEAN_SCRIPT="$PROJECT_ROOT/_crucible/clean.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

run_test() {
    ((TESTS_RUN++))
    local test_name="$1"
    log_info "Running test: $test_name"
}

setup_test_files() {
    cd "$PROJECT_ROOT"
    
    # Create a fake checkout.yaml
    cat > checkout.yaml << 'EOF'
mathlib4:
  github_org: leanprover-community
  github_repo: mathlib4
  sha: test123
batteries:
  github_org: leanprover-community
  github_repo: batteries
  sha: test456
EOF

    # Create some test directories (directories that exist in repositories.yml)
    mkdir -p mathlib4/some/content
    echo "test file" > mathlib4/test.txt
    mkdir -p batteries/other/content
    echo "another test file" > batteries/test2.txt
    mkdir -p plausible/content
    echo "plausible test" > plausible/test.txt
    # Create a directory not in repos file
    mkdir -p not_in_repos_file
    echo "should not be deleted" > not_in_repos_file/keep.txt
}

cleanup_all() {
    cd "$PROJECT_ROOT"
    rm -rf mathlib4 batteries plausible not_in_repos_file checkout.yaml 2>/dev/null || true
}

# Test 1: Clean with existing files (should succeed)
test_clean_with_existing_files() {
    run_test "Clean with existing files"
    cleanup_all
    setup_test_files
    
    if python3 "$CLEAN_SCRIPT"; then
        # Check that checkout.yaml was deleted
        if [[ ! -f "checkout.yaml" ]]; then
            # Check that repository directories were deleted
            if [[ ! -d "mathlib4" ]] && [[ ! -d "batteries" ]] && [[ ! -d "plausible" ]]; then
                # Check that directories not in repos file were NOT deleted
                if [[ -d "not_in_repos_file" ]] && [[ -f "not_in_repos_file/keep.txt" ]]; then
                    log_success "Clean properly removed tracked files and directories"
                    return 0
                else
                    log_failure "Clean incorrectly removed untracked directories"
                    return 1
                fi
            else
                log_failure "Clean failed to remove repository directories"
                return 1
            fi
        else
            log_failure "Clean failed to remove checkout.yaml"
            return 1
        fi
    else
        log_failure "Clean command failed unexpectedly"
        return 1
    fi
}

# Test 2: Clean with no files (should succeed gracefully)
test_clean_with_no_files() {
    run_test "Clean with no files to clean"
    cleanup_all
    
    if python3 "$CLEAN_SCRIPT"; then
        log_success "Clean handled missing files gracefully"
        return 0
    else
        log_failure "Clean failed when no files existed"
        return 1
    fi
}

# Test 3: Clean with partial directory set (some dirs exist, some don't)
test_clean_with_partial_directories() {
    run_test "Clean with partial directory set"
    cleanup_all
    setup_test_files
    
    # Remove one of the created directories before running clean
    rm -rf batteries
    
    if python3 "$CLEAN_SCRIPT"; then
        # Check that checkout.yaml was deleted
        if [[ ! -f "checkout.yaml" ]]; then
            # Check that existing repository directories were deleted
            if [[ ! -d "mathlib4" ]] && [[ ! -d "plausible" ]]; then
                # Check that directories not in repos file were NOT deleted
                if [[ -d "not_in_repos_file" ]] && [[ -f "not_in_repos_file/keep.txt" ]]; then
                    log_success "Clean properly handled mixed existing/non-existing directories"
                    return 0
                else
                    log_failure "Clean incorrectly removed untracked directories"
                    return 1
                fi
            else
                log_failure "Clean failed to remove existing repository directories"
                return 1
            fi
        else
            log_failure "Clean failed to remove checkout.yaml"
            return 1
        fi
    else
        log_failure "Clean command failed unexpectedly with partial directories"
        return 1
    fi
}

# Test 4: Clean via crucible command
test_clean_via_crucible_command() {
    run_test "Clean via crucible command"
    cleanup_all
    setup_test_files
    
    if "$PROJECT_ROOT/crucible" clean; then
        # Check that files were cleaned
        if [[ ! -f "checkout.yaml" ]] && [[ ! -d "mathlib4" ]] && [[ ! -d "batteries" ]] && [[ ! -d "plausible" ]]; then
            log_success "Clean via crucible command worked correctly"
            return 0
        else
            log_failure "Clean via crucible command failed to remove files"
            return 1
        fi
    else
        log_failure "Crucible clean command failed"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting _crucible/clean.py self-tests"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Clean script: $CLEAN_SCRIPT"
    
    # Verify the clean script exists
    if [[ ! -f "$CLEAN_SCRIPT" ]]; then
        log_failure "Clean script not found at $CLEAN_SCRIPT"
        exit 1
    fi
    
    # Verify repositories.yml exists (but don't modify it during testing)
    if [[ ! -f "$PROJECT_ROOT/_crucible/repositories.yml" ]]; then
        log_failure "repositories.yml not found at $PROJECT_ROOT/_crucible/repositories.yml"
        exit 1
    fi
    
    echo
    
    # Run all tests (don't exit on failure, collect results)
    test_clean_with_no_files || true
    test_clean_with_partial_directories || true
    test_clean_with_existing_files || true
    test_clean_via_crucible_command || true
    
    # Final cleanup
    cleanup_all
    
    # Summary
    echo
    log_info "Test Summary:"
    echo "  Tests run: $TESTS_RUN"
    echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ $TESTS_FAILED test(s) failed${NC}"
        exit 1
    fi
}

# Run the tests
main "$@" 