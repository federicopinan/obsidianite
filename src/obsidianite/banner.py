from __future__ import annotations

import importlib.metadata
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

# Get version from package metadata
try:
    __version__ = importlib.metadata.version("obsidianite")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

console = Console()

TITLE = '''
  ____  _         _     _ _             _ _       
 / __ \| |       (_)   | (_)           (_) |      
| |  | | |__  ___ _  __| |_  __ _ _ __  _| |_ ___ 
| |  | | '_ \/ __| |/ _` | |/ _` | '_ \| | __/ _ \\
| |__| | |_) \__ \ | (_| | | (_| | | | | | ||  __/
 \____/|_.__/|___/_|\__,_|_|\__,_|_| |_|_|\__\___|
'''

def print_banner(animated: bool = True) -> None:
    """Print the application banner with version."""
    console.print(Align.center(TITLE, vertical="middle"), style="purple")
    console.print(Align.right(f"v{__version__}"), style="purple")


