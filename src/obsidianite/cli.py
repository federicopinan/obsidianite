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
from git import Repo

from .banner import print_banner
from .config import get_token, set_token, set_repo_mapping, get_repo_mapping
from .github_api import get_or_create_private_repo, build_remote_url, get_latest_release
from .git_utils import init_repo, open_repo, commit_all, push as git_push, pull as git_pull, get_changed_files, get_diff_summary


console = Console()
app = typer.Typer(help="Sync your Obsidian vault with a private GitHub repo")


@app.callback()
def _main() -> None:
    print_banner(animated=True)
    console.print(Panel.fit("Manage your Obsidian vault backups", title="OBSIDIANITE", box=box.ROUNDED))


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
        typer.echo("Token stored in ~/.obsidianite/.env")
    else:
        typer.echo("Using existing GitHub token")

    if not repo_name:
        default_repo = vault_path.name.replace(" ", "-")
        repo_name = typer.prompt("Enter GitHub repository name", default=default_repo)
    
    typer.echo(f"{'Checking' if use_existing else 'Using'} repository: {repo_name}")

    try:
        full_name = get_or_create_private_repo(token, repo_name, create_if_missing=not use_existing)
        remote_url = build_remote_url(token, full_name)
        repo = init_repo(vault_path, remote_url)
        set_repo_mapping(vault_path, full_name, remote_url)
        console.success = lambda msg: console.print(f"[bold green]✓[/] {msg}")
        action = "Connected to" if use_existing else "Initialized"
        console.success(f"Vault {action} at {vault_path} → {full_name}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
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
            console.print("[yellow]No changes to commit.[/]")
            return
        
        # Create a table to show changes
        table = Table(title="Changes to be committed", box=box.ROUNDED)
        table.add_column("Status", style="cyan")
        table.add_column("Files", style="white")
        
        for status, files in changes.items():
            if files:
                table.add_row(
                    status.title(),
                    "\n".join(files)
                )
        
        console.print(table)
        
        # Ask for confirmation
        if not Confirm.ask("Do you want to commit and push these changes?"):
            console.print("[yellow]Operation cancelled.[/]")
            return
        
        with Status("[cyan]Committing changes...[/]", console=console):
            changed = commit_all(repo, message=message)
        
        if changed:
            with Status("[cyan]Pushing to GitHub...[/]", console=console):
                git_push(repo)
            console.print("[green]✓ Changes successfully pushed to GitHub[/]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)


@app.command()
def pull():
    """Pull and show latest changes from GitHub."""
    mapping = get_repo_mapping()
    if not mapping.get("VAULT_PATH"):
        raise typer.Exit("Vault not configured. Run 'obsidianite init'.")
    
    try:
        repo = open_repo(Path(mapping["VAULT_PATH"]))
        
        with Status("[cyan]Pulling latest changes...[/]", console=console):
            old_rev, new_rev = git_pull(repo)
        
        if old_rev == new_rev:
            console.print("[yellow]Already up to date.[/]")
            return
        
        # Get and display changes
        changes = get_diff_summary(repo, old_rev, new_rev)
        
        table = Table(title="Changes pulled from GitHub", box=box.ROUNDED)
        table.add_column("Status", style="cyan")
        table.add_column("Files", style="white")
        
        for status, files in changes.items():
            if files:
                table.add_row(
                    status.title(),
                    "\n".join(files)
                )
        
        console.print(table)
        console.print("[green]✓ Successfully pulled changes from GitHub[/]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)


@app.command()
def update():
    """Update Obsidianite to the latest version."""
    with Status("[cyan]Checking for updates...[/]", console=console):
        try:
            latest_version = get_latest_release()
            current_version = importlib.metadata.version("obsidianite")
            
            if latest_version == current_version:
                console.print("[yellow]You are already running the latest version![/]")
                return
                
            console.print(f"[cyan]New version available:[/] {latest_version}")
            console.print(f"[cyan]Current version:[/] {current_version}")
            
            if Confirm.ask("Do you want to update Obsidianite?"):
                with Status("[cyan]Updating Obsidianite...[/]", console=console):
                    # Use pip to update the package
                    import subprocess
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", 
                        "--upgrade", "obsidianite"
                    ])
                console.print("[green]✓ Obsidianite has been updated successfully![/]")
                console.print("[yellow]Please restart your terminal to use the new version.[/]")
            else:
                console.print("[yellow]Update cancelled.[/]")
                
        except Exception as e:
            console.print(f"[bold red]Error checking for updates:[/] {e}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


