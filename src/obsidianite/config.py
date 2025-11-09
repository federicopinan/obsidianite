from __future__ import annotations

import os
import stat
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


APP_DIR = Path(os.path.expanduser("~")) / ".obsidianite"
ENV_PATH = APP_DIR / ".env"
CONFIG_PATH = APP_DIR / "config"


def ensure_app_dirs() -> None:
    """Create app directories with secure permissions (0700)."""
    try:
        # Create directory with restrictive permissions atomically
        APP_DIR.mkdir(parents=True, exist_ok=False, mode=0o700)
    except FileExistsError:
        # Verify it's actually a directory and not a symlink attack
        if not APP_DIR.is_dir() or APP_DIR.is_symlink():
            raise RuntimeError(
                f"Security error: {APP_DIR} exists but is not a regular directory"
            )
        # Ensure correct permissions on existing directory
        if os.name != 'nt':  # Skip permission check on Windows
            os.chmod(APP_DIR, stat.S_IRWXU)  # 0700


def load_env() -> None:
    ensure_app_dirs()
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)


def get_token() -> Optional[str]:
    load_env()
    return os.getenv("GITHUB_TOKEN")


def set_token(token: str) -> None:
    """Store GitHub token with secure file permissions (0600).

    Args:
        token: GitHub personal access token to store

    Raises:
        ValueError: If token format is invalid
    """
    from .security import validate_github_token

    # Validate token format before storing
    token = validate_github_token(token)

    ensure_app_dirs()
    content = f"GITHUB_TOKEN={token}\n"

    # Write token file
    ENV_PATH.write_text(content, encoding="utf-8")

    # Set restrictive permissions (0600 - owner read/write only)
    if os.name != 'nt':  # Skip on Windows (uses different permission model)
        os.chmod(ENV_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        logging.info(f"Token file permissions set to 0600: {ENV_PATH}")


def set_repo_mapping(vault_path: Path, repo_full_name: str, remote_url: str) -> None:
    """Store repository mapping with secure permissions.

    Args:
        vault_path: Path to Obsidian vault
        repo_full_name: Full repository name (owner/repo)
        remote_url: Git remote URL (credentials will be sanitized)
    """
    from .security import sanitize_url_for_display

    ensure_app_dirs()

    # Sanitize URL to remove embedded credentials before storing
    safe_remote_url = sanitize_url_for_display(remote_url)

    lines = [
        f"VAULT_PATH={vault_path.as_posix()}",
        f"REPO_FULL_NAME={repo_full_name}",
        f"REMOTE_URL={safe_remote_url}",
        "",
    ]

    mapping_file = APP_DIR / "mapping.env"
    mapping_file.write_text("\n".join(lines), encoding="utf-8")

    # Set restrictive permissions (0600)
    if os.name != 'nt':  # Skip on Windows
        os.chmod(mapping_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600


def get_repo_mapping() -> dict[str, str]:
    """Load and validate repository mapping configuration.

    Returns:
        Dictionary containing vault path, repository name, and remote URL

    Raises:
        RuntimeError: If file permissions are insecure
    """
    path = APP_DIR / "mapping.env"
    if not path.exists():
        return {}

    # Verify file permissions for security
    if os.name != 'nt':  # Skip on Windows
        file_stat = path.stat()
        if file_stat.st_mode & 0o077:  # Check if others can read
            logging.warning(
                f"Insecure permissions on {path}. "
                "Run: chmod 600 ~/.obsidianite/mapping.env"
            )

    data: dict[str, str] = {}
    allowed_keys = {'VAULT_PATH', 'REPO_FULL_NAME', 'REMOTE_URL'}

    for line_num, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.strip().startswith("#"):
            continue

        if "=" not in line:
            logging.warning(f"Invalid line {line_num} in mapping.env: no '=' found")
            continue

        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()

        # Validate key names
        if k not in allowed_keys:
            logging.warning(f"Unknown configuration key: {k}")
            continue

        # Store validated values
        data[k] = v

    return data


