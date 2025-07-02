#!/usr/bin/env python3
"""
Outputs the current default branch SHAs for all repositories in crucible/repositories.yml as YAML to stdout.
"""

import sys
import yaml
import subprocess
import json
from pathlib import Path

def gh_api(path):
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"gh api {path} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)

def get_default_branch_sha(org, repo):
    repo_data = gh_api(f"repos/{org}/{repo}")
    default_branch = repo_data['default_branch']
    branch_data = gh_api(f"repos/{org}/{repo}/branches/{default_branch}")
    return branch_data['commit']['sha'], default_branch

def get_default_branches():
    repos_file = Path("_crucible/repositories.yml")
    if not repos_file.exists():
        print("Error: repositories.yml not found in _crucible directory", file=sys.stderr)
        sys.exit(1)
    with open(repos_file, 'r') as f:
        repos_data = yaml.safe_load(f)
    result = {}
    for repo_info in repos_data:
        name = repo_info['name']
        org = repo_info['github_org']
        repo = repo_info['github_repo']
        sha, branch = get_default_branch_sha(org, repo)
        result[name] = {
            'github_org': org,
            'github_repo': repo,
            'sha': sha,
            'branch': branch
        }
    return result

def main():
    result = get_default_branches()
    yaml.dump(result, sys.stdout, default_flow_style=False, indent=2)

if __name__ == "__main__":
    main() 