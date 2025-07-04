#!/usr/bin/env python3
"""
Modifies lakefile.lean or lakefile.toml in each repository subdirectory to use relative paths
for require statements, and creates/updates a root lakefile.toml that requires all repositories.

Usage:
  lakefile.py
"""

import os
import sys
import yaml
import re
import subprocess
import toml
from pathlib import Path
from typing import Dict, List, Optional, Union

# Add the parent directory to sys.path so we can import _crucible modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_repositories() -> List[Dict[str, str]]:
    """Load repository configuration from repositories.yml"""
    repos_file = Path("_crucible/repositories.yml")
    if not repos_file.exists():
        print("Error: repositories.yml not found in _crucible directory", file=sys.stderr)
        sys.exit(1)
    
    with open(repos_file, 'r') as f:
        return yaml.safe_load(f)

def find_lakefile(repo_dir: Path) -> Optional[Path]:
    """Find lakefile.toml or lakefile.lean in a repository directory"""
    toml_file = repo_dir / "lakefile.toml"
    lean_file = repo_dir / "lakefile.lean"
    
    if toml_file.exists():
        return toml_file
    elif lean_file.exists():
        return lean_file
    else:
        return None

def get_repository_names() -> Dict[str, str]:
    """Get mapping of repository names to their GitHub repo names"""
    repos = load_repositories()
    return {repo['name']: repo['github_repo'] for repo in repos}

def extract_package_name(lakefile_path: Path) -> Optional[str]:
    """Extract the actual package name from a lakefile"""
    try:
        if lakefile_path.name == "lakefile.toml":
            with open(lakefile_path, 'r') as f:
                data = toml.load(f)
            return data.get('name')
        else:  # lakefile.lean
            with open(lakefile_path, 'r') as f:
                content = f.read()
            # Look for package declaration: package <name> where
            package_match = re.search(r'package\s+([a-zA-Z0-9_]+)\s+where', content)
            if package_match:
                return package_match.group(1)
    except Exception as e:
        print(f"Warning: Could not extract package name from {lakefile_path}: {e}", file=sys.stderr)
    return None

def run_lake_update(repo_dir: Path, repo_name: str) -> bool:
    """Run 'lake update' in a repository directory"""
    try:
        print(f"  Running lake update in {repo_name}...")
        result = subprocess.run(
            ["lake", "update"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode == 0:
            print(f"  Lake update completed successfully in {repo_name}")
            return True
        else:
            print(f"  Lake update failed in {repo_name}: {result.stderr.strip()}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  Lake update timed out in {repo_name}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Error running lake update in {repo_name}: {e}", file=sys.stderr)
        return False

def modify_toml_lakefile(lakefile_path: Path, repo_name_map: Dict[str, str]) -> bool:
    """Modify a TOML lakefile to use relative paths for require statements"""
    try:
        with open(lakefile_path, 'r') as f:
            data = toml.load(f)
        
        modified = False
        
        # Check if there are require statements
        if 'require' in data:
            for require_entry in data['require']:
                if 'name' in require_entry:
                    req_name = require_entry['name']
                    
                    # Check if this is a repository we manage locally
                    if req_name in repo_name_map:
                        # Convert to relative path
                        relative_path = f"../{req_name}"
                        
                        # Remove git/url fields and set path
                        if 'git' in require_entry:
                            del require_entry['git']
                            modified = True
                        if 'url' in require_entry:
                            del require_entry['url']
                            modified = True
                        if 'rev' in require_entry:
                            del require_entry['rev']
                            modified = True
                        if 'version' in require_entry:
                            del require_entry['version']
                            modified = True
                        if 'scope' in require_entry:
                            del require_entry['scope']
                            modified = True
                        
                        # Set path if it's different
                        if require_entry.get('path') != relative_path:
                            require_entry['path'] = relative_path
                            modified = True
                            print(f"  Updated {req_name} to use path: {relative_path}")
        
        if modified:
            with open(lakefile_path, 'w') as f:
                toml.dump(data, f)
        
        return modified
        
    except Exception as e:
        print(f"Error modifying TOML lakefile {lakefile_path}: {e}", file=sys.stderr)
        return False

def modify_lean_lakefile(lakefile_path: Path, repo_name_map: Dict[str, str]) -> bool:
    """Modify a Lean lakefile to use relative paths for require statements"""
    try:
        with open(lakefile_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match require statements in Lean format
        # Matches: require "scope" / "name" @ git "url"
        # or: require <name> from git "<url>" @ "<rev>"
        # or: require <name> from "<path>"
        # etc.
        require_pattern = r'require\s+(?:"[^"]*"\s*/\s+"([^"]+)"|([a-zA-Z0-9_]+))(?:\s+@\s+git\s+"[^"]*"|\s+from\s+git\s+"[^"]*"(?:\s+@\s+"[^"]*")?|\s+from\s+"[^"]*")?'
        
        def replace_require(match):
            # Group 1: scoped name (e.g., "batteries" from "scope" / "batteries")
            # Group 2: simple name (e.g., mathlib4)
            req_name = match.group(1) if match.group(1) else match.group(2)
            
            if req_name in repo_name_map:
                relative_path = f"../{req_name}"
                replacement = f'require {req_name} from "{relative_path}"'
                print(f"  Updated {req_name} to use path: {relative_path}")
                return replacement
            else:
                # Keep the original if it's not a repo we manage
                return match.group(0)
        
        content = re.sub(require_pattern, replace_require, content)
        
        if content != original_content:
            with open(lakefile_path, 'w') as f:
                f.write(content)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error modifying Lean lakefile {lakefile_path}: {e}", file=sys.stderr)
        return False

def create_root_lakefile(repo_names: List[str]) -> None:
    """Create or update the root lakefile.toml that requires all repositories"""
    root_lakefile = Path("lakefile.toml")
    
    # Base configuration
    config = {
        'name': 'crucible-workspace',
        'version': '0.1.0',
        'require': []
    }
    
    # Load existing config if it exists
    if root_lakefile.exists():
        try:
            with open(root_lakefile, 'r') as f:
                existing_config = toml.load(f)
            
            # Preserve existing name and version if they exist
            if 'name' in existing_config:
                config['name'] = existing_config['name']
            if 'version' in existing_config:
                config['version'] = existing_config['version']
                
        except Exception as e:
            print(f"Warning: Could not read existing {root_lakefile}: {e}", file=sys.stderr)
    
    # Add require entries for each repository
    for repo_name in sorted(repo_names):
        repo_dir = Path(repo_name)
        if repo_dir.exists():
            # Find the lakefile and extract the actual package name
            lakefile_path = find_lakefile(repo_dir)
            if lakefile_path:
                package_name = extract_package_name(lakefile_path)
                if package_name:
                    require_entry = {
                        'name': package_name,
                        'path': f"./{repo_name}"
                    }
                    config['require'].append(require_entry)
                    print(f"Added {package_name} (from {repo_name}) to root lakefile")
                else:
                    print(f"Warning: Could not determine package name for {repo_name}, skipping")
            else:
                print(f"Warning: No lakefile found for {repo_name}, skipping")
    
    # Write the root lakefile
    try:
        with open(root_lakefile, 'w') as f:
            toml.dump(config, f)
        print(f"\nRoot lakefile.toml created/updated with {len(config['require'])} repositories")
    except Exception as e:
        print(f"Error writing root lakefile: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to modify all lakefiles"""
    print("Crucible Lakefile Modifier")
    print("=" * 30)
    
    # Load repository configuration
    repos = load_repositories()
    repo_name_map = get_repository_names()
    repo_names = [repo['name'] for repo in repos]
    
    print(f"Managing {len(repos)} repositories:")
    for repo in repos:
        print(f"  - {repo['name']}")
    print()
    
    # Process each repository
    total_modified = 0
    for repo in repos:
        repo_name = repo['name']
        repo_dir = Path(repo_name)
        
        if not repo_dir.exists():
            print(f"Repository {repo_name}: directory not found (run 'crucible checkout' first)")
            continue
        
        lakefile_path = find_lakefile(repo_dir)
        if not lakefile_path:
            print(f"Repository {repo_name}: no lakefile.toml or lakefile.lean found")
            continue
        
        print(f"Repository {repo_name}: processing {lakefile_path.name}")
        
        # Modify the lakefile based on its type
        if lakefile_path.name == "lakefile.toml":
            modified = modify_toml_lakefile(lakefile_path, repo_name_map)
        else:  # lakefile.lean
            modified = modify_lean_lakefile(lakefile_path, repo_name_map)
        
        if modified:
            total_modified += 1
            print(f"  Modified {lakefile_path}")
            # Run lake update after modifying the lakefile
            run_lake_update(repo_dir, repo_name)
        else:
            print(f"  No changes needed for {lakefile_path}")
        print()
    
    # Create root lakefile
    print("Creating root workspace lakefile...")
    create_root_lakefile(repo_names)
    
    # Run lake update in root directory to update the workspace manifest
    print("\nUpdating root workspace manifest...")
    root_update_success = run_lake_update(Path("."), "crucible-workspace")
    
    print(f"\nSummary:")
    print(f"  Modified {total_modified} repository lakefiles")
    print(f"  Created/updated root lakefile.toml")
    if root_update_success:
        print(f"  Updated workspace manifest successfully")
    else:
        print(f"  Warning: Workspace manifest update failed")
    print(f"\nAll lakefiles have been configured to use local relative paths.")

if __name__ == "__main__":
    main() 