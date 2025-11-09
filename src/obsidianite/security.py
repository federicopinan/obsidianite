"""Security utilities for input validation and sanitization."""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from rich.prompt import Confirm


def validate_github_token(token: str) -> str:
    """Validate GitHub token format.

    Args:
        token: GitHub personal access token

    Returns:
        Validated token string

    Raises:
        ValueError: If token format is invalid
    """
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string")

    token = token.strip()

    # GitHub tokens have specific formats:
    # - Classic PAT: ghp_[A-Za-z0-9]{36}
    # - Fine-grained PAT: github_pat_[A-Za-z0-9_]{82}
    # - OAuth: gho_[A-Za-z0-9]{36}
    # - Server-to-server: ghs_[A-Za-z0-9]{36}

    valid_patterns = [
        r'^ghp_[A-Za-z0-9]{36}$',           # Classic PAT
        r'^github_pat_[A-Za-z0-9_]{82}$',   # Fine-grained PAT
        r'^gho_[A-Za-z0-9]{36}$',           # OAuth
        r'^ghs_[A-Za-z0-9]{36}$',           # Server-to-server
    ]

    if not any(re.match(pattern, token) for pattern in valid_patterns):
        raise ValueError(
            "Invalid GitHub token format. Please ensure you're using a valid "
            "Personal Access Token from https://github.com/settings/tokens"
        )

    return token


def validate_repo_name(name: str) -> str:
    """Validate repository name against GitHub naming rules.

    Args:
        name: Repository name to validate

    Returns:
        Validated repository name

    Raises:
        ValueError: If repository name is invalid
    """
    if not name or len(name) > 100:
        raise ValueError("Repository name must be 1-100 characters")

    # GitHub repository name rules:
    # - Can contain alphanumeric, hyphens, underscores, periods
    # - Cannot start with special characters
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', name):
        raise ValueError(
            "Repository name can only contain alphanumeric characters, "
            "hyphens, underscores, and periods, and must start with alphanumeric"
        )

    # Prevent suspicious names
    forbidden = ['.git', '..', '__pycache__', 'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
    if any(forbidden_str in name.upper() for forbidden_str in forbidden):
        raise ValueError("Repository name contains forbidden patterns")

    return name


def validate_vault_path(path: Path) -> Path:
    """Validate and sanitize vault path to prevent path traversal.

    Args:
        path: Path to validate

    Returns:
        Validated and resolved absolute path

    Raises:
        ValueError: If path validation fails
    """
    # Expand and resolve to absolute path
    path = path.expanduser().resolve()

    # Ensure path is within user's home directory or explicitly allowed locations
    home = Path.home()
    try:
        # Check if path is relative to home (security boundary)
        path.relative_to(home)
    except ValueError:
        # Path is outside home directory - warn user
        from rich.console import Console
        console = Console()
        console.print(
            f"[yellow]Warning:[/] Path '{path}' is outside your home directory.",
            highlight=False
        )
        if not Confirm.ask("Continue anyway?", default=False):
            raise ValueError("Path validation failed: outside home directory")

    # Check for suspicious path components
    path_str = str(path)
    suspicious_chars = ['..', '$', '`', ';', '|', '&', '\n', '\r']
    if any(char in path_str for char in suspicious_chars):
        raise ValueError("Path contains potentially unsafe characters")

    return path


def validate_remote_url(url: str) -> str:
    """Validate and sanitize git remote URL.

    Args:
        url: Remote URL to validate

    Returns:
        Validated URL string

    Raises:
        ValueError: If URL validation fails
    """
    if not url:
        raise ValueError("Remote URL cannot be empty")

    # Parse URL to validate structure
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    # Only allow https and git schemes (SSH git@github.com URLs parse differently)
    if parsed.scheme and parsed.scheme not in ['https', 'git', 'ssh']:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    # Check for command injection attempts
    dangerous_chars = [';', '|', '&', '$', '`', '\n', '\r', '<', '>']
    if any(char in url for char in dangerous_chars):
        raise ValueError("URL contains potentially dangerous characters")

    # Validate it's a GitHub URL (optional - can be commented out for other Git hosts)
    if parsed.netloc and 'github.com' not in parsed.netloc.lower():
        from rich.console import Console
        console = Console()
        console.print(
            f"[yellow]Warning:[/] Remote URL is not GitHub ({parsed.netloc}).",
            highlight=False
        )
        if not Confirm.ask("Continue anyway?", default=False):
            raise ValueError("Remote URL validation failed: not a GitHub URL")

    return url


def sanitize_url_for_display(url: str) -> str:
    """Remove credentials from URL before displaying or storing.

    Args:
        url: URL that may contain credentials

    Returns:
        URL with credentials removed
    """
    # Remove user:pass@ from URL
    return re.sub(r'://[^@]+@', '://', url)


def sanitize_error_message(error: Exception, token: Optional[str] = None) -> str:
    """Sanitize error messages to prevent information disclosure.

    Args:
        error: Exception to sanitize
        token: Optional token to redact from error message

    Returns:
        Sanitized error message
    """
    error_str = str(error)

    # Remove tokens from error messages
    if token:
        error_str = error_str.replace(token, "***TOKEN***")

    # Remove token patterns even if token not provided
    token_patterns = [
        r'ghp_[A-Za-z0-9]{36}',
        r'github_pat_[A-Za-z0-9_]{82}',
        r'gho_[A-Za-z0-9]{36}',
        r'ghs_[A-Za-z0-9]{36}',
    ]
    for pattern in token_patterns:
        error_str = re.sub(pattern, '***TOKEN***', error_str)

    # Remove full file paths, keep only filename
    error_str = re.sub(r'/[^\s]+/([^/\s]+)', r'\1', error_str)

    return error_str


def validate_input_length(value: str, max_length: int, name: str) -> str:
    """Validate input length to prevent DoS.

    Args:
        value: Input string to validate
        max_length: Maximum allowed length
        name: Name of the input field (for error messages)

    Returns:
        Validated input string

    Raises:
        ValueError: If input exceeds maximum length
    """
    if len(value) > max_length:
        raise ValueError(
            f"{name} exceeds maximum length of {max_length} characters "
            f"(got {len(value)})"
        )
    return value


# Maximum input lengths
MAX_PATH_LENGTH = 4096
MAX_REPO_NAME_LENGTH = 100
MAX_COMMIT_MESSAGE_LENGTH = 1000
MAX_TOKEN_LENGTH = 255
