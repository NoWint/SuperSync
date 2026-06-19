import os
import platform


def get_platform() -> str:
    """Return the current platform: 'windows', 'macos', or 'linux'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    return system


def is_windows() -> bool:
    return get_platform() == "windows"


def is_macos() -> bool:
    return get_platform() == "macos"


def get_shell_config_files() -> list[str]:
    """Return the default shell config files for the current platform."""
    if is_windows():
        return [
            "Documents/PowerShell/Microsoft.PowerShell_profile.ps1",
            "Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
        ]
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return [".zshrc", ".zprofile"]
    elif "bash" in shell:
        return [".bashrc", ".bash_profile"]
    elif "fish" in shell:
        return [".config/fish/config.fish"]
    return [".zshrc", ".bashrc", ".bash_profile"]


def get_default_shell_config_file() -> str:
    """Return the primary shell config file name for the current platform."""
    if is_windows():
        return "Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return ".zshrc"
    elif "bash" in shell:
        return ".bashrc"
    elif "fish" in shell:
        return ".config/fish/config.fish"
    return ".zshrc"


def get_vscode_settings_path() -> str:
    """Return the relative path to VS Code settings.json for the current platform."""
    if is_windows():
        return "AppData/Roaming/Code/User/settings.json"
    return "Library/Application Support/Code/User/settings.json"


def get_dotfiles_paths() -> list[str]:
    """Return the default dotfile paths to scan for the current platform."""
    if is_windows():
        return [
            ".gitconfig",
            ".editorconfig",
            "Documents/PowerShell/Microsoft.PowerShell_profile.ps1",
            "AppData/Roaming/npm/.npmrc",
        ]
    return [
        ".zshrc",
        ".bashrc",
        ".bash_profile",
        ".gitconfig",
        ".gitignore_global",
        ".vimrc",
        ".editorconfig",
        ".config/starship.toml",
    ]
