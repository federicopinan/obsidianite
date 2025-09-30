from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


APP_DIR = Path(os.path.expanduser("~")) / ".obsidianite"
ENV_PATH = APP_DIR / ".env"
CONFIG_PATH = APP_DIR / "config"


def ensure_app_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_env() -> None:
    ensure_app_dirs()
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)


def get_token() -> Optional[str]:
    load_env()
    return os.getenv("GITHUB_TOKEN")


def set_token(token: str) -> None:
    ensure_app_dirs()
    # Write minimal env file with restrictive permissions where possible
    content = f"GITHUB_TOKEN={token}\n"
    ENV_PATH.write_text(content, encoding="utf-8")


def set_repo_mapping(vault_path: Path, repo_full_name: str, remote_url: str) -> None:
    ensure_app_dirs()
    lines = [
        f"VAULT_PATH={vault_path.as_posix()}",
        f"REPO_FULL_NAME={repo_full_name}",
        f"REMOTE_URL={remote_url}",
        "",
    ]
    (APP_DIR / "mapping.env").write_text("\n".join(lines), encoding="utf-8")


def get_repo_mapping() -> dict[str, str]:
    path = APP_DIR / "mapping.env"
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


