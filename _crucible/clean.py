#!/usr/bin/env python3
"""
Deletes checkout.yaml and all directories corresponding to repos listed in crucible/repositories.yml.
"""
import os
import shutil
import yaml
from pathlib import Path

def main():
    repos_file = Path("_crucible/repositories.yml")
    if not repos_file.exists():
        print("repositories.yml not found in _crucible directory.")
        return
    with open(repos_file, 'r') as f:
        repos_data = yaml.safe_load(f)
    # Delete checkout.yaml
    checkout_file = Path("checkout.yaml")
    if checkout_file.exists():
        print(f"Deleting {checkout_file}")
        checkout_file.unlink()
    else:
        print(f"{checkout_file} does not exist, skipping.")
    
    # Delete root lakefile.toml
    lakefile = Path("lakefile.toml")
    if lakefile.exists():
        print(f"Deleting {lakefile}")
        lakefile.unlink()
    else:
        print(f"{lakefile} does not exist, skipping.")
    
    # Delete root lake-manifest.json
    manifest = Path("lake-manifest.json")
    if manifest.exists():
        print(f"Deleting {manifest}")
        manifest.unlink()
    else:
        print(f"{manifest} does not exist, skipping.")
    
    # Delete lean-toolchain
    toolchain = Path("lean-toolchain")
    if toolchain.exists():
        print(f"Deleting {toolchain}")
        toolchain.unlink()
    else:
        print(f"{toolchain} does not exist, skipping.")
    
    # Delete each repo directory
    for repo_info in repos_data:
        name = repo_info['name']
        repo_dir = Path(name)
        if repo_dir.exists() and repo_dir.is_dir():
            print(f"Deleting directory {repo_dir}")
            shutil.rmtree(repo_dir)
        else:
            print(f"Directory {repo_dir} does not exist, skipping.")

if __name__ == "__main__":
    main() 