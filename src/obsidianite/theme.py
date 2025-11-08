"""Obsidian theme colors and styles for the CLI interface."""

from rich.theme import Theme
from rich.style import Style

# Obsidian Official Color Palette
# Based on Obsidian's default dark theme
OBSIDIAN_PURPLE = "#483699"       # Main purple accent (dark mode)
OBSIDIAN_PURPLE_HOVER = "#4d3ca6"  # Purple hover state
OBSIDIAN_PURPLE_LIGHT = "#7b6cd9"  # Light purple accent
OBSIDIAN_PURPLE_BRIGHT = "#8273e6" # Bright purple for highlights
OBSIDIAN_BLACK = "#0d0d0d"         # Deep black background
OBSIDIAN_GRAY = "#2e3134"          # Dark gray
OBSIDIAN_GRAY_LIGHT = "#525252"    # Light gray for borders

# UI Color Scheme
class ObsidianColors:
    """Color constants for Obsidian-themed CLI."""

    # Primary colors
    PRIMARY = OBSIDIAN_PURPLE
    PRIMARY_BRIGHT = OBSIDIAN_PURPLE_BRIGHT
    PRIMARY_LIGHT = OBSIDIAN_PURPLE_LIGHT

    # Status colors
    SUCCESS = "#10b981"    # Green for success
    WARNING = "#f59e0b"    # Amber for warnings
    ERROR = "#ef4444"      # Red for errors
    INFO = OBSIDIAN_PURPLE_LIGHT

    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a1a1aa"
    TEXT_MUTED = "#71717a"

    # Background colors
    BG_PRIMARY = OBSIDIAN_BLACK
    BG_PANEL = "#1a1a1a"
    BG_HOVER = "#262626"


# Rich Theme Configuration
obsidian_theme = Theme({
    "info": f"bold {ObsidianColors.INFO}",
    "warning": f"bold {ObsidianColors.WARNING}",
    "error": f"bold {ObsidianColors.ERROR}",
    "success": f"bold {ObsidianColors.SUCCESS}",
    "primary": f"bold {ObsidianColors.PRIMARY}",
    "primary.bright": f"bold {ObsidianColors.PRIMARY_BRIGHT}",
    "text.primary": ObsidianColors.TEXT_PRIMARY,
    "text.secondary": ObsidianColors.TEXT_SECONDARY,
    "text.muted": ObsidianColors.TEXT_MUTED,
})


def get_gradient_text(text: str) -> str:
    """Create a purple gradient effect for text using Obsidian colors."""
    # Simple gradient from dark to light purple
    colors = [
        OBSIDIAN_PURPLE,
        OBSIDIAN_PURPLE_HOVER,
        OBSIDIAN_PURPLE_LIGHT,
        OBSIDIAN_PURPLE_BRIGHT,
    ]

    lines = text.split('\n')
    result = []

    for i, line in enumerate(lines):
        color_index = i % len(colors)
        result.append(f"[{colors[color_index]}]{line}[/]")

    return '\n'.join(result)


def get_title_style() -> str:
    """Get the style for main titles."""
    return f"bold {ObsidianColors.PRIMARY_BRIGHT}"


def get_subtitle_style() -> str:
    """Get the style for subtitles."""
    return f"{ObsidianColors.PRIMARY_LIGHT}"


def get_border_style() -> str:
    """Get the style for borders."""
    return ObsidianColors.PRIMARY
