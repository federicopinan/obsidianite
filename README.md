# Obsidianite 🌑

Obsidianite is a powerful command-line tool designed to seamlessly sync your Obsidian vault with a private GitHub repository. It provides a beautiful CLI interface with Obsidian's signature purple and black theme, featuring automatic Git operations and secure token management.

## Features ✨

-   **Modern GUI** with Obsidian's signature dark purple theme
-   **Beautiful CLI interface** with gradient purple banner
-   Color-coded panels and tables for better readability
-   Real-time changes preview before push/pull
-   Visual repository status dashboard
-   Automatic Git repository management
-   Private GitHub repository integration
-   Secure token storage
-   Safe `.gitignore` configuration
-   Simple command structure

## Requirements 📋

-   Python 3.11 or higher
-   Git installed and configured on your system
-   GitHub account
-   Obsidian vault

## Installation 📦

### For Users

```bash
pip install obsidianite
```

### For Development

```bash
pip install -e .
```

## Usage 🚀

Obsidianite provides both a graphical interface and command-line tools:

### GUI Mode (Recommended)

```bash
obsidianite-gui    # Launch the graphical interface
```

The GUI provides an intuitive interface with:
- Visual vault initialization
- Real-time changes preview
- Easy push/pull operations
- Repository status dashboard
- All styled with Obsidian's signature purple theme

### CLI Mode

```bash
obsidianite init    # Initialize a new vault with Git and GitHub
obsidianite push   # Push your changes to GitHub
obsidianite pull   # Pull latest changes from GitHub
obsidianite update # Update both local and remote changes
```

## Security 🔒

Obsidianite takes security seriously:

-   Creates private GitHub repositories by default
-   Stores GitHub tokens securely in `~/.obsidianite/.env`
-   Generates a secure `.gitignore` for your vault
-   Uses HTTPS for all GitHub operations

## Configuration 🔧

Configuration is managed through a simple and intuitive system:

-   Secure token storage in `~/.obsidianite/.env`
-   Vault-to-repository mappings
-   Obsidian-themed visual interface

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
