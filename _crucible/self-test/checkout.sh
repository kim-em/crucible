#!/bin/bash

# Self-test script for crucible/checkout.py
# Tests all three modes: -f, --stdin, and default

# Note: Don't use set -e since we test failure cases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECKOUT_SCRIPT="$PROJECT_ROOT/_crucible/checkout.py"

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

cleanup_test_files() {
    # Clean up any test directories and files
    rm -rf mathlib4 batteries plausible LeanSearchClient importGraph proofwidgets aesop Qq Cli
    rm -f checkout.yaml
}

setup_test_environment() {
    cd "$PROJECT_ROOT"
    cleanup_test_files
}

# Test 1: File mode with invalid SHA (should fail)
test_file_mode_invalid_sha() {
    run_test "File mode with invalid SHA"
    setup_test_environment
    
    if python3 "$CHECKOUT_SCRIPT" -f "_crucible/self-test/test_invalid_sha.yaml" 2>/dev/null; then
        log_failure "Expected failure with invalid SHA, but command succeeded"
        return 1
    else
        log_success "Correctly failed with invalid SHA"
        return 0
    fi
}

# Test 2: File mode with valid SHA (should succeed)
test_file_mode_valid_sha() {
    run_test "File mode with valid SHA"
    setup_test_environment
    
    if python3 "$CHECKOUT_SCRIPT" -f "_crucible/self-test/test_valid_old_sha.yaml"; then
        # Check if checkout.yaml was created
        if [[ -f "checkout.yaml" ]]; then
            # Check if at least one directory was created
            if [[ -d "mathlib4" ]] || [[ -d "batteries" ]]; then
                log_success "File mode with valid SHA worked correctly"
                return 0
            else
                log_failure "checkout.yaml created but no directories found"
                return 1
            fi
        else
            log_failure "checkout.yaml was not created"
            return 1
        fi
    else
        log_failure "Command failed unexpectedly with valid SHA"
        return 1
    fi
}

# Test 3: Stdin mode with invalid SHA (should fail)
test_stdin_mode_invalid_sha() {
    run_test "Stdin mode with invalid SHA"
    setup_test_environment
    
    if cat "_crucible/self-test/test_invalid_sha.yaml" | python3 "$CHECKOUT_SCRIPT" --stdin 2>/dev/null; then
        log_failure "Expected failure with invalid SHA via stdin, but command succeeded"
        return 1
    else
        log_success "Correctly failed with invalid SHA via stdin"
        return 0
    fi
}

# Test 4: Stdin mode with valid SHA (should succeed)
test_stdin_mode_valid_sha() {
    run_test "Stdin mode with valid SHA"
    setup_test_environment
    
    if cat "_crucible/self-test/test_valid_old_sha.yaml" | python3 "$CHECKOUT_SCRIPT" --stdin; then
        # Check if checkout.yaml was created
        if [[ -f "checkout.yaml" ]]; then
            # Check if at least one directory was created
            if [[ -d "mathlib4" ]] || [[ -d "batteries" ]]; then
                log_success "Stdin mode with valid SHA worked correctly"
                return 0
            else
                log_failure "checkout.yaml created but no directories found"
                return 1
            fi
        else
            log_failure "checkout.yaml was not created"
            return 1
        fi
    else
        log_failure "Command failed unexpectedly with valid SHA via stdin"
        return 1
    fi
}

# Test 5: Default mode (should succeed)
test_default_mode() {
    run_test "Default mode (using default_branches.py)"
    setup_test_environment
    
    if python3 "$CHECKOUT_SCRIPT"; then
        # Check if checkout.yaml was created
        if [[ -f "checkout.yaml" ]]; then
            # Check if multiple directories were created (default should create many)
            local dir_count=0
            for dir in mathlib4 batteries plausible LeanSearchClient importGraph proofwidgets aesop Qq Cli; do
                if [[ -d "$dir" ]]; then
                    ((dir_count++))
                fi
            done
            
            if [[ $dir_count -ge 3 ]]; then
                log_success "Default mode worked correctly (created $dir_count directories)"
                return 0
            else
                log_failure "Default mode created only $dir_count directories (expected ≥3)"
                return 1
            fi
        else
            log_failure "checkout.yaml was not created in default mode"
            return 1
        fi
    else
        log_failure "Default mode command failed unexpectedly"
        return 1
    fi
}

# Test 6: Help option
test_help_option() {
    run_test "Help option"
    
    if python3 "$CHECKOUT_SCRIPT" --help >/dev/null 2>&1; then
        log_success "Help option works correctly"
        return 0
    else
        log_failure "Help option failed"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting crucible checkout.py self-tests"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Checkout script: $CHECKOUT_SCRIPT"
    
    # Verify the checkout script exists
    if [[ ! -f "$CHECKOUT_SCRIPT" ]]; then
        log_failure "Checkout script not found at $CHECKOUT_SCRIPT"
        exit 1
    fi
    
    echo
    
    # Run all tests (don't exit on failure, collect results)
    test_help_option || true
    test_file_mode_invalid_sha || true
    test_stdin_mode_invalid_sha || true
    test_file_mode_valid_sha || true
    test_stdin_mode_valid_sha || true
    test_default_mode || true
    
    # Final cleanup
    setup_test_environment
    
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