#!/usr/bin/env python3
"""
Checks out repositories at specified SHAs from YAML input and writes checkout.yaml.

Usage:
  checkout.py -f file.yaml      # Read SHAs from specified file
  checkout.py --stdin           # Read YAML from stdin
  checkout.py                   # Use default branches from default_branches.py
"""

import os
import sys
import yaml
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
import argparse

# Add the parent directory to sys.path so we can import _crucible.default_branches
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _crucible.default_branches import get_default_branches

def download_repo_contents(org, repo, sha, target_dir):
    """Download repository contents as a zip file and extract to target directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_url = f"https://github.com/{org}/{repo}/archive/{sha}.zip"
        zip_path = os.path.join(temp_dir, f"{repo}.zip")
        print(f"Downloading {zip_url}...")
        response = requests.get(zip_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download {zip_url}: {response.status_code}")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        extracted_dir = None
        for item in os.listdir(temp_dir):
            if item.startswith(f"{repo}-"):
                extracted_dir = os.path.join(temp_dir, item)
                break
        if not extracted_dir:
            raise Exception(f"Could not find extracted directory for {repo}")
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.move(extracted_dir, target_dir)



def main():
    parser = argparse.ArgumentParser(description="Check out repositories at specified SHAs")
    parser.add_argument('-f', '--file', type=str, help='YAML file containing repository SHAs')
    parser.add_argument('--stdin', action='store_true', help='Read YAML from stdin')
    
    args = parser.parse_args()
    
    if args.file:
        # Read from specified file
        print(f"Reading repository SHAs from {args.file}...", file=sys.stderr)
        with open(args.file, 'r') as f:
            repos_data = yaml.safe_load(f)
    elif args.stdin:
        # Read from stdin
        print("Reading YAML from stdin...", file=sys.stderr)
        input_yaml = sys.stdin.read()
        if not input_yaml.strip():
            print("Error: No YAML provided on stdin", file=sys.stderr)
            sys.exit(1)
        repos_data = yaml.safe_load(input_yaml)
    else:
        # Use default branches
        print("No file or stdin specified, using _crucible/default_branches.py to get default SHAs...", file=sys.stderr)
        repos_data = get_default_branches()

    # Load existing checkout info from disk if available (before any changes)
    existing_checkout = {}
    if os.path.exists("checkout.yaml"):
        with open("checkout.yaml", "r") as f:
            existing_checkout = yaml.safe_load(f) or {}

    errors = []

    # For each repo, check out at the specified SHA if needed
    for name, info in repos_data.items():
        org = info['github_org']
        repo = info['github_repo']
        sha = info['sha']
        current_sha = existing_checkout.get(name, {}).get('sha')
        if current_sha == sha:
            print(f"\nRepository {name} is already at SHA {sha}, skipping...")
            continue
        print(f"\nProcessing {name} ({org}/{repo}) at SHA {sha}...")
        try:
            target_dir = Path(name)
            download_repo_contents(org, repo, sha, target_dir)
            print(f"  Downloaded to {target_dir}")
        except Exception as e:
            error_msg = f"  Error processing {name}: {e}"
            print(error_msg)
            errors.append(error_msg)
            continue

    # Write the desired YAML to checkout.yaml
    with open("checkout.yaml", 'w') as f:
        yaml.dump(repos_data, f, default_flow_style=False, indent=2)
    print("\nCheckout information written to checkout.yaml")
    print("Repository contents have been downloaded to subdirectories.")

    # Print error summary and exit code
    if errors:
        print("\nSummary of errors:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\nAll repositories checked out successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main() 