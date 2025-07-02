#!/usr/bin/env python3
"""
Script to checkout repositories from repositories.yml and dump their contents
into subdirectories without git history, recording the SHA in checkout.yaml.
"""

import os
import sys
import json
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urljoin


def get_default_branch_sha(org, repo):
    """Get the SHA of the default branch for a repository."""
    api_url = f"https://api.github.com/repos/{org}/{repo}"
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to get repo info for {org}/{repo}: {response.status_code}")
    
    repo_data = response.json()
    default_branch = repo_data['default_branch']
    
    # Get the SHA of the default branch
    branch_url = f"{api_url}/branches/{default_branch}"
    branch_response = requests.get(branch_url)
    if branch_response.status_code != 200:
        raise Exception(f"Failed to get branch info for {org}/{repo}: {branch_response.status_code}")
    
    branch_data = branch_response.json()
    return branch_data['commit']['sha']


def download_repo_contents(org, repo, sha, target_dir):
    """Download repository contents as a zip file and extract to target directory."""
    # Create a temporary directory for the zip file
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_url = f"https://github.com/{org}/{repo}/archive/{sha}.zip"
        zip_path = os.path.join(temp_dir, f"{repo}.zip")
        
        print(f"Downloading {zip_url}...")
        response = requests.get(zip_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download {zip_url}: {response.status_code}")
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the extracted directory (it will be named repo-sha)
        extracted_dir = None
        for item in os.listdir(temp_dir):
            if item.startswith(f"{repo}-"):
                extracted_dir = os.path.join(temp_dir, item)
                break
        
        if not extracted_dir:
            raise Exception(f"Could not find extracted directory for {repo}")
        
        # Remove the target directory if it exists
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # Move the contents to the target directory
        shutil.move(extracted_dir, target_dir)


def main():
    # Read repositories.yml
    repos_file = Path("repositories.yml")
    if not repos_file.exists():
        print("Error: repositories.yml not found in current directory")
        sys.exit(1)
    
    with open(repos_file, 'r') as f:
        repos_data = json.load(f)
    
    # Create scripts directory if it doesn't exist
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    checkout_info = {}
    
    for repo_info in repos_data:
        name = repo_info['name']
        org = repo_info['github_org']
        repo = repo_info['github_repo']
        
        print(f"\nProcessing {name} ({org}/{repo})...")
        
        try:
            # Get the SHA of the default branch
            sha = get_default_branch_sha(org, repo)
            print(f"  Default branch SHA: {sha}")
            
            # Create target directory
            target_dir = Path(name)
            target_dir.mkdir(exist_ok=True)
            
            # Download and extract repository contents
            download_repo_contents(org, repo, sha, target_dir)
            print(f"  Downloaded to {target_dir}")
            
            # Record the checkout information
            checkout_info[name] = {
                'github_org': org,
                'github_repo': repo,
                'sha': sha,
                'branch': 'default'  # We're always getting the default branch
            }
            
        except Exception as e:
            print(f"  Error processing {name}: {e}")
            continue
    
    # Write checkout.yaml
    checkout_file = Path("checkout.yaml")
    with open(checkout_file, 'w') as f:
        json.dump(checkout_info, f, indent=2)
    
    print(f"\nCheckout information written to {checkout_file}")
    print("Repository contents have been downloaded to subdirectories.")


if __name__ == "__main__":
    main() 