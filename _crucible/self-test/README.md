# Crucible Checkout Self-Test

This directory contains comprehensive self-tests for the `crucible/checkout.py` script.

## Running the Tests

```bash
# Using the main crucible command (recommended)
python3 crucible.py self-test            # Run all tests
python3 crucible.py self-test checkout   # Run specific test

# Or directly
./crucible/self-test/checkout.sh
```

## What Gets Tested

The test suite validates all three modes of operation:

### 1. File Mode (`-f`)
- ✅ **Valid SHA**: Tests reading from a YAML file with valid repository SHAs
- ❌ **Invalid SHA**: Tests proper error handling when SHAs don't exist

### 2. Stdin Mode (`--stdin`)
- ✅ **Valid SHA**: Tests reading YAML from stdin with valid repository SHAs  
- ❌ **Invalid SHA**: Tests proper error handling when SHAs don't exist

### 3. Default Mode (no arguments)
- ✅ **Default branches**: Tests using `default_branches.py` to get current HEAD SHAs

### 4. Help Mode
- ✅ **Help option**: Tests that `--help` works correctly

## Test Files

- `test_invalid_sha.yaml` - Contains invalid SHAs for error testing
- `test_valid_old_sha.yaml` - Contains valid but older SHAs (v4.0.0, v4.2.0)
- `checkout.sh` - Checkout functionality test runner script

## Verification

Each test verifies:
- Exit codes (success/failure as expected)
- File creation (`checkout.yaml`)
- Directory creation (repository downloads)
- Error handling and reporting

## Output

The test suite provides colored output:
- 🟡 **[INFO]** - Test information and progress
- 🟢 **[PASS]** - Successful test cases
- 🔴 **[FAIL]** - Failed test cases

All tests clean up after themselves, removing downloaded repositories and `checkout.yaml` files. 