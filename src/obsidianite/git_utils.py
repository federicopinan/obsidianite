from __future__ import annotations

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from .security import validate_remote_url


GITIGNORE_CONTENT = """
# Obsidianite defaults
.env
.DS_Store
Thumbs.db
node_modules/
.obsidian/workspace
.obsidian/workspace.json
.obsidian/plugins/**/node_modules/
.obsidian/plugins/**/data.json
.obsidian/cache/
.trash/
*.code-workspace
*.swp
*.swo
""".strip()


def ensure_gitignore(path: Path) -> None:
    """Create .gitignore file with secure permissions if it doesn't exist.

    Args:
        path: Path to the repository root
    """
    gi = path / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE_CONTENT + "\n", encoding="utf-8")
        # Set appropriate permissions (0644 - owner rw, group/others r)
        if os.name != 'nt':  # Skip on Windows
            os.chmod(gi, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0644


def init_repo(vault_path: Path, remote_url: str) -> Repo:
    """Initialize a Git repository with secure settings.

    Args:
        vault_path: Path to the repository
        remote_url: Remote URL (will be validated)

    Returns:
        Initialized Repo object

    Raises:
        ValueError: If remote URL is invalid
        RuntimeError: If repository initialization fails
    """
    # Validate remote URL before using it
    remote_url = validate_remote_url(remote_url)

    ensure_gitignore(vault_path)
    try:
        if (vault_path / ".git").exists():
            repo = Repo(vault_path)
        else:
            repo = Repo.init(vault_path)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        raise RuntimeError(f"Cannot initialize repo at {vault_path}: {e}") from e

    # Clean up existing origin if it exists
    try:
        if "origin" in [r.name for r in repo.remotes]:
            repo.delete_remote("origin")
    except Exception:
        pass  # Ignore errors during remote cleanup

    # Create new remote
    repo.create_remote("origin", remote_url)

    # Initialize repository if needed
    if repo.is_dirty(untracked_files=True) or not repo.head.is_valid():
        try:
            repo.git.add(all=True)
            repo.index.commit("Initial commit by Obsidianite")
            repo.git.gc()  # Clean up any dangling objects
        except Exception as e:
            raise RuntimeError(f"Failed to initialize repository: {e}") from e

    try:
        repo.git.branch("-M", "main")
    except GitCommandError:
        pass
    try:
        repo.git.push("-u", "origin", "main")
    except GitCommandError:
        try:
            repo.git.push("origin", "HEAD:main")
            repo.git.push("-u", "origin", "main")
        except GitCommandError as e:
            raise RuntimeError(f"Failed to push initial commit: {e}") from e
    return repo


def commit_all(repo: Repo, message: Optional[str] = None) -> bool:
    try:
        repo.git.add(all=True)
        if message is None:
            message = f"obsidianite: update {datetime.now().isoformat(timespec='seconds')}"
        if repo.is_dirty(index=True, working_tree=True, untracked_files=True):
            repo.index.commit(message)
            # Clean up after commit
            repo.git.gc()
            return True
        return False
    finally:
        # Always ensure we clean up handles
        repo.close()


def push(repo: Repo) -> None:
    try:
        # Force garbage collection before push to clean up handles
        repo.git.gc()
        repo.git.push("origin", "HEAD:main")
    except GitCommandError as e:
        raise RuntimeError(f"Push failed: {e}") from e
    finally:
        # Ensure we clean up any remaining handles
        repo.close()


def pull(repo: Repo) -> Tuple[str, str]:
    """Pull changes and return old and new commit hashes for diff."""
    try:
        # Store current commit hash
        old_rev = repo.head.commit.hexsha
        
        # Force garbage collection before pull to clean up handles
        repo.git.gc()
        try:
            repo.git.pull("--rebase", "origin", "main")
        except GitCommandError:
            repo.git.pull("origin", "main")
            
        # Get new commit hash
        new_rev = repo.head.commit.hexsha
        return old_rev, new_rev
    except GitCommandError as e:
        raise RuntimeError(f"Pull failed: {e}") from e
    finally:
        # Ensure we clean up any remaining handles
        repo.close()


def get_changed_files(repo: Repo) -> Dict[str, List[str]]:
    """Get lists of changed files by status."""
    changed = {
        "modified": [],
        "added": [],
        "deleted": [],
        "renamed": [],
        "untracked": []
    }
    
    try:
        # Get changes between working tree and index
        diff = repo.index.diff(None)
        
        # Categorize changes
        for d in diff:
            if d.renamed:
                changed["renamed"].append(f"{d.a_path} → {d.b_path}")
            elif d.deleted_file:
                changed["deleted"].append(d.a_path)
            elif d.new_file:
                changed["added"].append(d.b_path)
            else:
                changed["modified"].append(d.a_path)
                
        # Get untracked files
        changed["untracked"] = repo.untracked_files
        
    except Exception as e:
        print(f"Error getting changed files: {e}")
        
    return changed


def get_diff_summary(repo: Repo, old_rev: str, new_rev: str) -> Dict[str, List[str]]:
    """Get a summary of changes between two revisions."""
    changes = {
        "modified": [],
        "added": [],
        "deleted": [],
        "renamed": []
    }
    
    try:
        # Get diff between revisions
        diff_index = repo.commit(old_rev).diff(new_rev)
        
        for diff in diff_index:
            if diff.renamed:
                changes["renamed"].append(f"{diff.a_path} → {diff.b_path}")
            elif diff.deleted_file:
                changes["deleted"].append(diff.a_path)
            elif diff.new_file:
                changes["added"].append(diff.b_path)
            else:
                changes["modified"].append(diff.a_path)
                
    except Exception as e:
        print(f"Error getting diff summary: {e}")
        
    return changes


def open_repo(vault_path: Path) -> Repo:
    return Repo(vault_path)


