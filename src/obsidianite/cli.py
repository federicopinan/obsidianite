from __future__ import annotations

from pathlib import Path
from typing import Optional, List
import sys
import importlib.metadata

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich import box
from rich.live import Live
from rich.status import Status
from rich.text import Text
from git import Repo

from .banner import print_banner
from .config import get_token, set_token, set_repo_mapping, get_repo_mapping
from .github_api import get_or_create_private_repo, build_remote_url, get_latest_release
from .git_utils import init_repo, open_repo, commit_all, push as git_push, pull as git_pull, get_changed_files, get_diff_summary
from .theme import ObsidianColors


console = Console()
app = typer.Typer(help="Sync your Obsidian vault with a private GitHub repo")


@app.callback()
def _main() -> None:
    print_banner(animated=True)
    panel_text = Text("Manage your Obsidian vault backups", style=f"{ObsidianColors.TEXT_PRIMARY}")
    console.print(Panel.fit(
        panel_text,
        title=f"[bold {ObsidianColors.PRIMARY_BRIGHT}]OBSIDIANITE[/]",
        border_style=ObsidianColors.PRIMARY,
        box=box.ROUNDED
    ))


@app.command()
def init(
    vault_path: Optional[Path] = typer.Option(None, "--vault", help="Path to local Obsidian vault"),
    repo_name: Optional[str] = typer.Option(None, "--repo", help="GitHub repository name"),
    use_existing: bool = typer.Option(False, "--use-existing", help="Use existing repository only, don't create new"),
):
    """Initialize a vault and connect it to a private GitHub repository."""
    if vault_path is None:
        vault_path = Path(typer.prompt("Enter local path of your Obsidian Vault"))
    vault_path = vault_path.expanduser().resolve()
    vault_path.mkdir(parents=True, exist_ok=True)

    token = get_token()
    if not token:
        token = typer.prompt("Enter your GitHub Personal Access Token", hide_input=True)
        set_token(token)
        console.print(f"[{ObsidianColors.SUCCESS}]✓[/] Token stored in ~/.obsidianite/.env")
    else:
        console.print(f"[{ObsidianColors.INFO}]ℹ[/] Using existing GitHub token")

    if not repo_name:
        default_repo = vault_path.name.replace(" ", "-")
        repo_name = typer.prompt("Enter GitHub repository name", default=default_repo)

    console.print(f"[{ObsidianColors.INFO}]{'Checking' if use_existing else 'Using'} repository:[/] [{ObsidianColors.PRIMARY_BRIGHT}]{repo_name}[/]")

    try:
        full_name = get_or_create_private_repo(token, repo_name, create_if_missing=not use_existing)
        remote_url = build_remote_url(token, full_name)
        repo = init_repo(vault_path, remote_url)
        set_repo_mapping(vault_path, full_name, remote_url)
        action = "Connected to" if use_existing else "Initialized"

        # Create success panel
        success_message = Text()
        success_message.append("✓ ", style=f"bold {ObsidianColors.SUCCESS}")
        success_message.append(f"Vault {action}\n", style=f"{ObsidianColors.TEXT_PRIMARY}")
        success_message.append(f"  Location: ", style=f"{ObsidianColors.TEXT_SECONDARY}")
        success_message.append(f"{vault_path}\n", style=f"{ObsidianColors.PRIMARY_LIGHT}")
        success_message.append(f"  Repository: ", style=f"{ObsidianColors.TEXT_SECONDARY}")
        success_message.append(f"{full_name}", style=f"{ObsidianColors.PRIMARY_LIGHT}")

        console.print(Panel(
            success_message,
            border_style=ObsidianColors.SUCCESS,
            box=box.ROUNDED
        ))
    except Exception as e:
        console.print(Panel(
            f"[bold {ObsidianColors.ERROR}]Error:[/] {e}",
            border_style=ObsidianColors.ERROR,
            box=box.ROUNDED
        ))
        raise typer.Exit(code=1)


@app.command()
def push(message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message")):
    """Preview, commit and push all local changes."""
    mapping = get_repo_mapping()
    if not mapping.get("VAULT_PATH"):
        raise typer.Exit("Vault not configured. Run 'obsidianite init'.")
    
    try:
        repo = open_repo(Path(mapping["VAULT_PATH"]))
        
        # Get and display changes
        changes = get_changed_files(repo)
        has_changes = any(changes.values())

        if not has_changes:
            console.print(Panel(
                f"[{ObsidianColors.WARNING}]ℹ No changes to commit.[/]",
                border_style=ObsidianColors.WARNING,
                box=box.ROUNDED
            ))
            return

        # Create a table to show changes
        table = Table(
            title=f"[bold {ObsidianColors.PRIMARY_BRIGHT}]Changes to be committed[/]",
            box=box.ROUNDED,
            border_style=ObsidianColors.PRIMARY
        )
        table.add_column("Status", style=f"bold {ObsidianColors.PRIMARY_LIGHT}")
        table.add_column("Files", style=f"{ObsidianColors.TEXT_PRIMARY}")

        for status, files in changes.items():
            if files:
                table.add_row(
                    status.title(),
                    "\n".join(files)
                )

        console.print(table)

        # Ask for confirmation
        if not Confirm.ask("Do you want to commit and push these changes?"):
            console.print(f"[{ObsidianColors.WARNING}]Operation cancelled.[/]")
            return

        with Status(f"[{ObsidianColors.PRIMARY_LIGHT}]Committing changes...[/]", console=console):
            changed = commit_all(repo, message=message)

        if changed:
            with Status(f"[{ObsidianColors.PRIMARY_LIGHT}]Pushing to GitHub...[/]", console=console):
                git_push(repo)
            console.print(Panel(
                f"[bold {ObsidianColors.SUCCESS}]✓ Changes successfully pushed to GitHub[/]",
                border_style=ObsidianColors.SUCCESS,
                box=box.ROUNDED
            ))

    except Exception as e:
        console.print(Panel(
            f"[bold {ObsidianColors.ERROR}]Error:[/] {e}",
            border_style=ObsidianColors.ERROR,
            box=box.ROUNDED
        ))
        raise typer.Exit(code=1)


@app.command()
def pull():
    """Pull and show latest changes from GitHub."""
    mapping = get_repo_mapping()
    if not mapping.get("VAULT_PATH"):
        raise typer.Exit("Vault not configured. Run 'obsidianite init'.")
    
    try:
        repo = open_repo(Path(mapping["VAULT_PATH"]))

        with Status(f"[{ObsidianColors.PRIMARY_LIGHT}]Pulling latest changes...[/]", console=console):
            old_rev, new_rev = git_pull(repo)

        if old_rev == new_rev:
            console.print(Panel(
                f"[{ObsidianColors.INFO}]✓ Already up to date.[/]",
                border_style=ObsidianColors.INFO,
                box=box.ROUNDED
            ))
            return

        # Get and display changes
        changes = get_diff_summary(repo, old_rev, new_rev)

        table = Table(
            title=f"[bold {ObsidianColors.PRIMARY_BRIGHT}]Changes pulled from GitHub[/]",
            box=box.ROUNDED,
            border_style=ObsidianColors.PRIMARY
        )
        table.add_column("Status", style=f"bold {ObsidianColors.PRIMARY_LIGHT}")
        table.add_column("Files", style=f"{ObsidianColors.TEXT_PRIMARY}")

        for status, files in changes.items():
            if files:
                table.add_row(
                    status.title(),
                    "\n".join(files)
                )

        console.print(table)
        console.print(Panel(
            f"[bold {ObsidianColors.SUCCESS}]✓ Successfully pulled changes from GitHub[/]",
            border_style=ObsidianColors.SUCCESS,
            box=box.ROUNDED
        ))

    except Exception as e:
        console.print(Panel(
            f"[bold {ObsidianColors.ERROR}]Error:[/] {e}",
            border_style=ObsidianColors.ERROR,
            box=box.ROUNDED
        ))
        raise typer.Exit(code=1)


@app.command()
def update():
    """Update Obsidianite to the latest version."""
    with Status(f"[{ObsidianColors.PRIMARY_LIGHT}]Checking for updates...[/]", console=console):
        try:
            latest_version = get_latest_release()
            current_version = importlib.metadata.version("obsidianite")

            if latest_version == current_version:
                console.print(Panel(
                    f"[{ObsidianColors.SUCCESS}]✓ You are already running the latest version![/]",
                    border_style=ObsidianColors.SUCCESS,
                    box=box.ROUNDED
                ))
                return

            # Create update info panel
            update_info = Text()
            update_info.append("Update Available\n\n", style=f"bold {ObsidianColors.PRIMARY_BRIGHT}")
            update_info.append("Current version: ", style=f"{ObsidianColors.TEXT_SECONDARY}")
            update_info.append(f"{current_version}\n", style=f"{ObsidianColors.TEXT_PRIMARY}")
            update_info.append("New version: ", style=f"{ObsidianColors.TEXT_SECONDARY}")
            update_info.append(f"{latest_version}", style=f"bold {ObsidianColors.PRIMARY_LIGHT}")

            console.print(Panel(
                update_info,
                border_style=ObsidianColors.INFO,
                box=box.ROUNDED
            ))

            if Confirm.ask("Do you want to update Obsidianite?"):
                with Status(f"[{ObsidianColors.PRIMARY_LIGHT}]Updating Obsidianite...[/]", console=console):
                    # Use pip to update the package
                    import subprocess
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install",
                        "--upgrade", "obsidianite"
                    ])

                success_msg = Text()
                success_msg.append("✓ ", style=f"bold {ObsidianColors.SUCCESS}")
                success_msg.append("Obsidianite has been updated successfully!\n", style=f"{ObsidianColors.TEXT_PRIMARY}")
                success_msg.append("Please restart your terminal to use the new version.", style=f"{ObsidianColors.TEXT_SECONDARY}")

                console.print(Panel(
                    success_msg,
                    border_style=ObsidianColors.SUCCESS,
                    box=box.ROUNDED
                ))
            else:
                console.print(f"[{ObsidianColors.WARNING}]Update cancelled.[/]")

        except Exception as e:
            console.print(Panel(
                f"[bold {ObsidianColors.ERROR}]Error checking for updates:[/] {e}",
                border_style=ObsidianColors.ERROR,
                box=box.ROUNDED
            ))
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


