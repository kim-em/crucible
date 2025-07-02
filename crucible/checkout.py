#!/usr/bin/env python3
"""
Checks out repositories at specified SHAs from YAML input (stdin or from default_branches.py), and writes checkout.yaml.
"""

import os
import sys
import yaml
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
import importlib.util

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

def import_get_default_branches():
    # Try to import scripts.default_branches.get_default_branches
    try:
        from scripts.default_branches import get_default_branches
        return get_default_branches
    except ImportError:
        # Fallback: import by path
        import importlib.util
        script_path = os.path.join(os.path.dirname(__file__), 'default_branches.py')
        spec = importlib.util.spec_from_file_location("default_branches", script_path)
        if spec is None or spec.loader is None:
            raise ImportError("Could not load default_branches.py module spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.get_default_branches

def main():
    # Always read stdin
    input_yaml = sys.stdin.read()
    if input_yaml.strip():
        repos_data = yaml.safe_load(input_yaml)
    else:
        print("No YAML on stdin, using crucible/default_branches.py to get default SHAs...", file=sys.stderr)
        from crucible.default_branches import get_default_branches
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