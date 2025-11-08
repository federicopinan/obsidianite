from __future__ import annotations

import importlib.metadata
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from .theme import ObsidianColors, get_gradient_text

# Get version from package metadata
try:
    __version__ = importlib.metadata.version("obsidianite")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

console = Console()

TITLE = '''
  ██████╗ ██████╗ ███████╗██╗██████╗ ██╗ █████╗ ███╗   ██╗██╗████████╗███████╗
 ██╔═══██╗██╔══██╗██╔════╝██║██╔══██╗██║██╔══██╗████╗  ██║██║╚══██╔══╝██╔════╝
 ██║   ██║██████╔╝███████╗██║██║  ██║██║███████║██╔██╗ ██║██║   ██║   █████╗
 ██║   ██║██╔══██╗╚════██║██║██║  ██║██║██╔══██║██║╚██╗██║██║   ██║   ██╔══╝
 ╚██████╔╝██████╔╝███████║██║██████╔╝██║██║  ██║██║ ╚████║██║   ██║   ███████╗
  ╚═════╝ ╚═════╝ ╚══════╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝   ╚══════╝
'''

SUBTITLE = "  Sync your Obsidian vault with GitHub  "
DECORATION = "─" * 80

def print_banner(animated: bool = True) -> None:
    """Print the application banner with version."""
    # Create gradient effect for the title
    title_text = Text()
    lines = TITLE.strip().split('\n')

    for i, line in enumerate(lines):
        if i < 2:
            color = ObsidianColors.PRIMARY_BRIGHT
        elif i < 4:
            color = ObsidianColors.PRIMARY_LIGHT
        else:
            color = ObsidianColors.PRIMARY

        title_text.append(line + "\n", style=f"bold {color}")

    console.print(Align.center(title_text))

    # Print version and subtitle with Obsidian colors
    version_text = Text(f"v{__version__}", style=f"bold {ObsidianColors.PRIMARY_LIGHT}")
    subtitle_text = Text(SUBTITLE, style=f"{ObsidianColors.TEXT_SECONDARY}")

    console.print(Align.center(subtitle_text))
    console.print(Align.center(f"[{ObsidianColors.PRIMARY}]{DECORATION}[/]"))
    console.print(Align.center(version_text))
    console.print()  # Add spacing
