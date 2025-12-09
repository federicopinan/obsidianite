"""GUI interface for Obsidianite using CustomTkinter with Obsidian theme."""

from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
import threading
from typing import Optional
from tkinter import filedialog, messagebox
import sys

from .config import get_token, set_token, set_repo_mapping, get_repo_mapping
from .github_api import get_or_create_private_repo, build_remote_url
from .git_utils import init_repo, open_repo, commit_all, push as git_push, pull as git_pull, get_changed_files, get_diff_summary
from .theme import ObsidianColors


# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ObsidianiteGUI:
    """Main GUI application for Obsidianite."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Obsidianite - Obsidian Vault Sync")
        self.root.geometry("900x700")

        # Configure Obsidian colors
        self.root.configure(fg_color="#0d0d0d")

        # Create main container
        self.main_container = ctk.CTkFrame(self.root, fg_color="#0d0d0d")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create header
        self.create_header()

        # Create navigation menu
        self.create_navigation()

        # Create content area
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a", corner_radius=10)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Show init panel by default
        self.current_panel = None
        self.show_init_panel()

    def create_header(self):
        """Create the header with Obsidianite branding."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a", corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 10))

        # Title with Obsidian purple
        title = ctk.CTkLabel(
            header_frame,
            text="🌑 OBSIDIANITE",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#8273e6"
        )
        title.pack(pady=20)

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Sync your Obsidian vault with GitHub",
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        )
        subtitle.pack(pady=(0, 20))

    def create_navigation(self):
        """Create navigation buttons."""
        nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 10))

        button_config = {
            "height": 40,
            "corner_radius": 8,
            "font": ctk.CTkFont(size=14, weight="bold"),
            "fg_color": "#483699",
            "hover_color": "#7b6cd9",
        }

        # Init button
        self.init_btn = ctk.CTkButton(
            nav_frame,
            text="⚙️ Initialize Vault",
            command=self.show_init_panel,
            **button_config
        )
        self.init_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Push button
        self.push_btn = ctk.CTkButton(
            nav_frame,
            text="⬆️ Push Changes",
            command=self.show_push_panel,
            **button_config
        )
        self.push_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Pull button
        self.pull_btn = ctk.CTkButton(
            nav_frame,
            text="⬇️ Pull Changes",
            command=self.show_pull_panel,
            **button_config
        )
        self.pull_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Status button
        self.status_btn = ctk.CTkButton(
            nav_frame,
            text="📊 Status",
            command=self.show_status_panel,
            **button_config
        )
        self.status_btn.pack(side="left", padx=5, expand=True, fill="x")

    def clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_init_panel(self):
        """Show the initialization panel."""
        self.clear_content()
        self.current_panel = "init"

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Initialize Your Vault",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8273e6"
        )
        title.pack(pady=(0, 20))

        # Vault path selection
        vault_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        vault_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            vault_frame,
            text="Obsidian Vault Path:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        path_container = ctk.CTkFrame(vault_frame, fg_color="transparent")
        path_container.pack(fill="x", padx=15, pady=(0, 15))

        self.vault_path_entry = ctk.CTkEntry(
            path_container,
            placeholder_text="Select your Obsidian vault folder...",
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#1a1a1a",
            border_color="#483699"
        )
        self.vault_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            path_container,
            text="Browse",
            width=100,
            height=40,
            fg_color="#483699",
            hover_color="#7b6cd9",
            command=self.browse_vault_path
        )
        browse_btn.pack(side="right")

        # GitHub token
        token_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        token_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            token_frame,
            text="GitHub Personal Access Token:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        # Check if token exists
        existing_token = get_token()
        if existing_token:
            token_status = ctk.CTkLabel(
                token_frame,
                text="✓ Token already configured",
                font=ctk.CTkFont(size=12),
                text_color="#10b981"
            )
            token_status.pack(anchor="w", padx=15, pady=(0, 15))
        else:
            self.token_entry = ctk.CTkEntry(
                token_frame,
                placeholder_text="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                height=40,
                font=ctk.CTkFont(size=12),
                fg_color="#1a1a1a",
                border_color="#483699",
                show="*"
            )
            self.token_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Repository name
        repo_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        repo_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            repo_frame,
            text="GitHub Repository Name:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.repo_name_entry = ctk.CTkEntry(
            repo_frame,
            placeholder_text="my-obsidian-vault",
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#1a1a1a",
            border_color="#483699"
        )
        self.repo_name_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Use existing repo checkbox
        self.use_existing_var = ctk.BooleanVar(value=False)
        use_existing_check = ctk.CTkCheckBox(
            scroll_frame,
            text="Use existing repository (don't create new)",
            variable=self.use_existing_var,
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa",
            fg_color="#483699",
            hover_color="#7b6cd9"
        )
        use_existing_check.pack(pady=10)

        # Initialize button
        init_btn = ctk.CTkButton(
            scroll_frame,
            text="Initialize Vault",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#483699",
            hover_color="#7b6cd9",
            command=self.initialize_vault
        )
        init_btn.pack(pady=20, fill="x")

        # Status label
        self.init_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.init_status_label.pack(pady=10)

    def browse_vault_path(self):
        """Open file dialog to select vault path."""
        path = filedialog.askdirectory(title="Select Obsidian Vault Folder")
        if path:
            self.vault_path_entry.delete(0, "end")
            self.vault_path_entry.insert(0, path)

    def initialize_vault(self):
        """Initialize the vault with GitHub."""
        vault_path = self.vault_path_entry.get().strip()
        repo_name = self.repo_name_entry.get().strip()

        if not vault_path:
            messagebox.showerror("Error", "Please select a vault path")
            return

        if not repo_name:
            messagebox.showerror("Error", "Please enter a repository name")
            return

        # Check for token
        token = get_token()
        if not token:
            if not hasattr(self, 'token_entry'):
                messagebox.showerror("Error", "No token found")
                return
            token = self.token_entry.get().strip()
            if not token:
                messagebox.showerror("Error", "Please enter a GitHub token")
                return
            set_token(token)

        self.init_status_label.configure(text="Initializing vault...", text_color="#8273e6")

        def init_thread():
            try:
                vault_path_obj = Path(vault_path).expanduser().resolve()
                vault_path_obj.mkdir(parents=True, exist_ok=True)

                use_existing = self.use_existing_var.get()
                full_name = get_or_create_private_repo(token, repo_name, create_if_missing=not use_existing)
                remote_url = build_remote_url(token, full_name)
                repo = init_repo(vault_path_obj, remote_url)
                set_repo_mapping(vault_path_obj, full_name, remote_url)

                self.root.after(0, lambda: self.init_status_label.configure(
                    text=f"✓ Successfully initialized vault!\nRepository: {full_name}",
                    text_color="#10b981"
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Vault initialized successfully!\n\nVault: {vault_path}\nRepository: {full_name}"
                ))
            except Exception as e:
                self.root.after(0, lambda: self.init_status_label.configure(
                    text=f"✗ Error: {str(e)}",
                    text_color="#ef4444"
                ))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=init_thread, daemon=True).start()

    def show_push_panel(self):
        """Show the push changes panel."""
        self.clear_content()
        self.current_panel = "push"

        # Check if vault is configured
        mapping = get_repo_mapping()
        if not mapping.get("VAULT_PATH"):
            self.show_not_configured_message()
            return

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Push Changes to GitHub",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8273e6"
        )
        title.pack(pady=(0, 20))

        # Commit message
        msg_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        msg_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            msg_frame,
            text="Commit Message (optional):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.commit_msg_entry = ctk.CTkEntry(
            msg_frame,
            placeholder_text="Update vault...",
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#1a1a1a",
            border_color="#483699"
        )
        self.commit_msg_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Changes preview
        self.changes_text = ctk.CTkTextbox(
            scroll_frame,
            height=300,
            font=ctk.CTkFont(family="monospace", size=11),
            fg_color="#1a1a1a",
            border_color="#483699",
            border_width=2
        )
        self.changes_text.pack(fill="both", expand=True, pady=10)

        # Buttons
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)

        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Refresh Changes",
            height=40,
            fg_color="#262626",
            hover_color="#3a3a3a",
            command=self.refresh_changes
        )
        refresh_btn.pack(side="left", padx=5, expand=True, fill="x")

        push_btn = ctk.CTkButton(
            button_frame,
            text="⬆️ Push to GitHub",
            height=40,
            fg_color="#483699",
            hover_color="#7b6cd9",
            command=self.push_changes
        )
        push_btn.pack(side="right", padx=5, expand=True, fill="x")

        # Status label
        self.push_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.push_status_label.pack(pady=10)

        # Load changes
        self.refresh_changes()

    def refresh_changes(self):
        """Refresh the list of changes."""
        mapping = get_repo_mapping()
        vault_path = mapping.get("VAULT_PATH")

        if not vault_path:
            return

        self.changes_text.delete("1.0", "end")
        self.push_status_label.configure(text="Loading changes...", text_color="#8273e6")

        def load_thread():
            try:
                repo = open_repo(Path(vault_path))
                changes = get_changed_files(repo)

                output = []
                has_changes = False

                for status, files in changes.items():
                    if files:
                        has_changes = True
                        output.append(f"\n{status.upper()}:\n")
                        for file in files:
                            output.append(f"  • {file}\n")

                if not has_changes:
                    output = ["No changes to commit."]

                self.root.after(0, lambda: self.changes_text.insert("1.0", "".join(output)))
                self.root.after(0, lambda: self.push_status_label.configure(
                    text="Changes loaded" if has_changes else "No changes to commit",
                    text_color="#10b981" if has_changes else "#f59e0b"
                ))
            except Exception as e:
                self.root.after(0, lambda: self.push_status_label.configure(
                    text=f"Error: {str(e)}",
                    text_color="#ef4444"
                ))

        threading.Thread(target=load_thread, daemon=True).start()

    def push_changes(self):
        """Push changes to GitHub."""
        mapping = get_repo_mapping()
        vault_path = mapping.get("VAULT_PATH")

        if not vault_path:
            return

        commit_msg = self.commit_msg_entry.get().strip() or None

        self.push_status_label.configure(text="Pushing changes...", text_color="#8273e6")

        def push_thread():
            try:
                repo = open_repo(Path(vault_path))

                # Check if there are changes
                changes = get_changed_files(repo)
                has_changes = any(changes.values())

                if not has_changes:
                    self.root.after(0, lambda: self.push_status_label.configure(
                        text="No changes to commit",
                        text_color="#f59e0b"
                    ))
                    self.root.after(0, lambda: messagebox.showinfo("Info", "No changes to commit"))
                    return

                # Commit and push
                changed = commit_all(repo, message=commit_msg)
                if changed:
                    git_push(repo)
                    self.root.after(0, lambda: self.push_status_label.configure(
                        text="✓ Changes successfully pushed to GitHub!",
                        text_color="#10b981"
                    ))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Changes successfully pushed to GitHub!"))
                    self.root.after(0, self.refresh_changes)
                else:
                    self.root.after(0, lambda: self.push_status_label.configure(
                        text="No changes to push",
                        text_color="#f59e0b"
                    ))

            except Exception as e:
                self.root.after(0, lambda: self.push_status_label.configure(
                    text=f"Error: {str(e)}",
                    text_color="#ef4444"
                ))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=push_thread, daemon=True).start()

    def show_pull_panel(self):
        """Show the pull changes panel."""
        self.clear_content()
        self.current_panel = "pull"

        # Check if vault is configured
        mapping = get_repo_mapping()
        if not mapping.get("VAULT_PATH"):
            self.show_not_configured_message()
            return

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Pull Changes from GitHub",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8273e6"
        )
        title.pack(pady=(0, 20))

        # Changes preview
        self.pull_changes_text = ctk.CTkTextbox(
            scroll_frame,
            height=400,
            font=ctk.CTkFont(family="monospace", size=11),
            fg_color="#1a1a1a",
            border_color="#483699",
            border_width=2
        )
        self.pull_changes_text.pack(fill="both", expand=True, pady=10)
        self.pull_changes_text.insert("1.0", "Click 'Pull from GitHub' to fetch latest changes...")

        # Pull button
        pull_btn = ctk.CTkButton(
            scroll_frame,
            text="⬇️ Pull from GitHub",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#483699",
            hover_color="#7b6cd9",
            command=self.pull_changes
        )
        pull_btn.pack(pady=20, fill="x")

        # Status label
        self.pull_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.pull_status_label.pack(pady=10)

    def pull_changes(self):
        """Pull changes from GitHub."""
        mapping = get_repo_mapping()
        vault_path = mapping.get("VAULT_PATH")

        if not vault_path:
            return

        self.pull_status_label.configure(text="Pulling changes...", text_color="#8273e6")
        self.pull_changes_text.delete("1.0", "end")
        self.pull_changes_text.insert("1.0", "Fetching changes from GitHub...\n")

        def pull_thread():
            try:
                repo = open_repo(Path(vault_path))
                old_rev, new_rev = git_pull(repo)

                if old_rev == new_rev:
                    self.root.after(0, lambda: self.pull_changes_text.delete("1.0", "end"))
                    self.root.after(0, lambda: self.pull_changes_text.insert("1.0", "✓ Already up to date."))
                    self.root.after(0, lambda: self.pull_status_label.configure(
                        text="Already up to date",
                        text_color="#10b981"
                    ))
                    self.root.after(0, lambda: messagebox.showinfo("Info", "Already up to date"))
                    return

                # Get changes
                changes = get_diff_summary(repo, old_rev, new_rev)

                output = ["\n✓ Successfully pulled changes from GitHub!\n\n"]

                for status, files in changes.items():
                    if files:
                        output.append(f"{status.upper()}:\n")
                        for file in files:
                            output.append(f"  • {file}\n")
                        output.append("\n")

                self.root.after(0, lambda: self.pull_changes_text.delete("1.0", "end"))
                self.root.after(0, lambda: self.pull_changes_text.insert("1.0", "".join(output)))
                self.root.after(0, lambda: self.pull_status_label.configure(
                    text="✓ Successfully pulled changes!",
                    text_color="#10b981"
                ))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Changes successfully pulled from GitHub!"))

            except Exception as e:
                self.root.after(0, lambda: self.pull_status_label.configure(
                    text=f"Error: {str(e)}",
                    text_color="#ef4444"
                ))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=pull_thread, daemon=True).start()

    def show_status_panel(self):
        """Show the status panel."""
        self.clear_content()
        self.current_panel = "status"

        # Check if vault is configured
        mapping = get_repo_mapping()
        if not mapping.get("VAULT_PATH"):
            self.show_not_configured_message()
            return

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Vault Status",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8273e6"
        )
        title.pack(pady=(0, 20))

        # Configuration info
        info_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        info_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            info_frame,
            text="Current Configuration",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#8273e6"
        ).pack(anchor="w", padx=15, pady=(15, 10))

        vault_path = mapping.get("VAULT_PATH", "Not configured")
        repo_name = mapping.get("REPO_NAME", "Not configured")

        info_text = f"""Vault Path: {vault_path}
Repository: {repo_name}
Token: {'✓ Configured' if get_token() else '✗ Not configured'}"""

        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color="#ffffff",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Repository status
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="#262626", corner_radius=8)
        status_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            status_frame,
            text="Repository Status",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#8273e6"
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.status_text = ctk.CTkTextbox(
            status_frame,
            height=200,
            font=ctk.CTkFont(family="monospace", size=11),
            fg_color="#1a1a1a",
        )
        self.status_text.pack(fill="both", padx=15, pady=(0, 15))

        # Load status
        self.load_status()

    def load_status(self):
        """Load repository status."""
        mapping = get_repo_mapping()
        vault_path = mapping.get("VAULT_PATH")

        if not vault_path:
            return

        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "Loading status...\n")

        def status_thread():
            try:
                repo = open_repo(Path(vault_path))
                changes = get_changed_files(repo)

                output = []
                has_changes = False

                for status, files in changes.items():
                    if files:
                        has_changes = True
                        output.append(f"\n{status.upper()} ({len(files)} files):\n")
                        for file in files[:10]:  # Show first 10
                            output.append(f"  • {file}\n")
                        if len(files) > 10:
                            output.append(f"  ... and {len(files) - 10} more\n")

                if not has_changes:
                    output = ["✓ Working directory clean - no changes to commit"]
                else:
                    output.insert(0, f"⚠ You have uncommitted changes:\n")

                self.root.after(0, lambda: self.status_text.delete("1.0", "end"))
                self.root.after(0, lambda: self.status_text.insert("1.0", "".join(output)))

            except Exception as e:
                self.root.after(0, lambda: self.status_text.delete("1.0", "end"))
                self.root.after(0, lambda: self.status_text.insert("1.0", f"Error: {str(e)}"))

        threading.Thread(target=status_thread, daemon=True).start()

    def show_not_configured_message(self):
        """Show message when vault is not configured."""
        message_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        message_frame.pack(expand=True)

        ctk.CTkLabel(
            message_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48)
        ).pack(pady=20)

        ctk.CTkLabel(
            message_frame,
            text="Vault Not Configured",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f59e0b"
        ).pack(pady=10)

        ctk.CTkLabel(
            message_frame,
            text="Please initialize your vault first",
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        ).pack(pady=5)

        ctk.CTkButton(
            message_frame,
            text="Go to Initialize",
            height=40,
            fg_color="#483699",
            hover_color="#7b6cd9",
            command=self.show_init_panel
        ).pack(pady=20)

    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI."""
    app = ObsidianiteGUI()
    app.run()


if __name__ == "__main__":
    main()
