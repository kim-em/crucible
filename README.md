# Crucible

A cross-repository pull request testing tool for Lean 4 projects, designed to help test PRs across multiple repositories at specific commit SHAs.

## Quick Start

### Installation

Clone this repository and ensure you have the required dependencies:

```bash
git clone https://github.com/kim-em/crucible
pip install pyyaml requests
```

### Basic Usage

```bash
# Show help
./crucible

# Check out repositories using default branches
./crucible checkout

# Check out from a specific file
./crucible checkout -f repos.yaml

# Check out from stdin
echo "repo_config..." | ./crucible checkout --stdin

# Clean up test repositories
./crucible clean

# Run self-tests
./crucible self-test
```

## Commands

### `crucible checkout [OPTIONS]`
Downloads repositories at specified commit SHAs.

**Options:**
- `-f FILE` - Read repository SHAs from YAML file
- `--stdin` - Read YAML configuration from stdin  
- No arguments - Use default branches from GitHub

**Example YAML format:**
```yaml
mathlib4:
  github_org: leanprover-community
  github_repo: mathlib4
  sha: fb81db9b3272fe1a876c07ff09214a03b5f4fdaf
  branch: master
```

### `crucible clean`
Removes all downloaded repository directories and `checkout.yaml`.

### `crucible self-test [TEST]`
Runs the test suite to verify functionality.

**Options:**
- `checkout` - Run checkout functionality tests
- `clean` - Run clean functionality tests
- No arguments - Run all available tests

## Repository Configuration

The `_crucible/repositories.yml` file defines the repositories that can be managed:

```yaml
- name: mathlib4
  github_org: leanprover-community
  github_repo: mathlib4
- name: batteries  
  github_org: leanprover-community
  github_repo: batteries
```

## Development

### Running Tests

```bash
# Run all tests
./crucible self-test

# Run specific test suites
./crucible self-test checkout
./crucible self-test clean
```

### GitHub Actions

This repository includes a CI workflow that automatically runs the self-test suite on all pushes and pull requests.

## Files Structure

- `crucible` - Main command dispatcher
- `_crucible/checkout.py` - Repository checkout functionality
- `_crucible/clean.py` - Cleanup functionality  
- `_crucible/default_branches.py` - GitHub API integration
- `_crucible/repositories.yml` - Repository definitions
- `_crucible/self-test/` - Test suite
  - `checkout.sh` - Checkout functionality tests
  - `clean.sh` - Clean functionality tests
- `.github/workflows/test.yml` - CI configuration 