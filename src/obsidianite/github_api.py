from __future__ import annotations

from typing import Optional
import re

from github import Github, GithubException

from .security import validate_github_token, validate_repo_name

# Repository where Obsidianite releases are published
OBSIDIANITE_REPO = "federicopinan/obsidianite"  # Ajusta esto a tu repositorio real


def check_repo_exists(token: str, repo_name: str) -> Optional[str]:
    """Check if a repository exists and return its full name if it does.

    Args:
        token: GitHub personal access token
        repo_name: Repository name to check

    Returns:
        Full repository name (owner/repo) if exists, None otherwise

    Raises:
        ValueError: If token or repository name format is invalid
    """
    # Validate inputs
    token = validate_github_token(token)
    repo_name = validate_repo_name(repo_name)

    gh = Github(token, verify=True, timeout=30)  # Explicit SSL verification and timeout
    try:
        user = gh.get_user()
        repo = user.get_repo(repo_name)
        return repo.full_name
    except GithubException:
        return None

def get_or_create_private_repo(token: str, repo_name: str, create_if_missing: bool = True) -> str:
    """Return full_name of a private repo, creating if missing and allowed.

    Args:
        token: GitHub token
        repo_name: Name of the repository
        create_if_missing: If True, create the repo if it doesn't exist. If False, raise an error.

    Returns:
        Full repository name (owner/repo)

    Raises:
        ValueError: If token or repository name format is invalid
        RuntimeError: If authentication fails or repository cannot be created

    The repository is created under the authenticated user's account.
    """
    # Validate inputs
    token = validate_github_token(token)
    repo_name = validate_repo_name(repo_name)

    gh = Github(token, verify=True, timeout=30)  # Explicit SSL verification and timeout
    try:
        user = gh.get_user()
    except GithubException as e:
        raise RuntimeError(f"GitHub authentication failed: {e}") from e

    try:
        repo = user.get_repo(repo_name)
        return repo.full_name
    except GithubException:
        if not create_if_missing:
            raise RuntimeError(f"Repository '{repo_name}' not found and creation not allowed")
        try:
            repo = user.create_repo(name=repo_name, private=True, auto_init=False)
            return repo.full_name
        except GithubException as e:
            raise RuntimeError(f"Failed to create repository '{repo_name}': {e}") from e


def build_remote_url(token: str, full_name: str) -> str:
    """Build git remote URL with embedded token for authentication.

    Args:
        token: GitHub personal access token
        full_name: Full repository name (owner/repo)

    Returns:
        HTTPS git remote URL with embedded credentials

    Note:
        The token is embedded in the URL for git operations.
        This URL should NEVER be logged or displayed to users.
        When storing in config files, use sanitize_url_for_display() to remove credentials.

    Security Warning:
        Embedding tokens in URLs is a security risk. The token can be exposed in:
        - Git config files
        - Process lists
        - Error messages
        - Shell history
        Future versions should migrate to SSH keys or git credential helpers.
    """
    from .security import validate_github_token

    # Validate token
    token = validate_github_token(token)

    # Validate repository name format (owner/repo)
    if not re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+$', full_name):
        raise ValueError(f"Invalid repository name format: {full_name}")

    # Use token-based HTTPS URL. Username can be "x-access-token" per Git recs
    return f"https://{token}:x-oauth-basic@github.com/{full_name}.git"


def get_latest_release() -> str:
    """Get the latest release version of Obsidianite."""
    gh = Github()
    try:
        repo = gh.get_repo(OBSIDIANITE_REPO)
        latest_release = repo.get_latest_release()
        
        # Extract version number from release tag
        version_match = re.match(r"v?(\d+\.\d+\.\d+)", latest_release.tag_name)
        if version_match:
            return version_match.group(1)
        
        return latest_release.tag_name.lstrip("v")
    except GithubException as e:
        raise RuntimeError(f"Failed to check for updates: {e}") from e


