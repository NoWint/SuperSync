from dataclasses import dataclass
from enum import Enum
from typing import Optional

from supersync.utils.run import run_command


class InstallStatus(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class InstallResult:
    name: str
    status: InstallStatus
    message: str = ""


class Installer:
    """Handles package installation for various package managers."""

    def _get_installed_version(self, manager: str, name: str) -> Optional[str]:
        """Check if a package is already installed and return its version."""
        if manager == "brew":
            result = run_command("brew", "list", "--formula", "--versions", name, check=False)
            if result.returncode == 0 and name in result.stdout:
                # Output format: "name version"
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return parts[-1]
            result = run_command("brew", "list", "--cask", "--versions", name, check=False)
            if result.returncode == 0 and name in result.stdout:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return parts[-1]
        elif manager == "winget":
            result = run_command("winget", "list", "--id", name, "--source", "winget", "--disable-interactivity", check=False)
            if result.returncode == 0 and name in result.stdout:
                # Parse version from winget list output
                for line in result.stdout.strip().split("\n"):
                    if name in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[-1]
        elif manager == "scoop":
            result = run_command("scoop", "list", check=False)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == name:
                        return parts[1]
        elif manager == "pip":
            result = run_command("pip", "show", name, check=False)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
        elif manager == "npm":
            result = run_command("npm", "list", "-g", name, "--depth=0", "--json", check=False)
            if result.returncode == 0:
                import json
                try:
                    data = json.loads(result.stdout)
                    deps = data.get("dependencies", {})
                    if name in deps:
                        return deps[name].get("version")
                except (json.JSONDecodeError, KeyError):
                    pass
        return None

    def install_brew_formula(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("brew", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            # upgrade
            result = run_command("brew", "upgrade", name, check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            # If upgrade fails, try install
            result = run_command("brew", "install", name, check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("brew", "install", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        if "already installed" in result.stderr.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_brew_cask(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("brew", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            # upgrade
            result = run_command("brew", "upgrade", "--cask", name, check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            # If upgrade fails, try install
            result = run_command("brew", "install", "--cask", name, check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("brew", "install", "--cask", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        if "already installed" in result.stderr.lower() or "already installed" in result.stdout.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_pip_package(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("pip", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            # upgrade
            result = run_command("pip", "install", "--upgrade", f"{name}=={version}", check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("pip", "install", f"{name}=={version}", check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        if "already satisfied" in result.stdout.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_npm_package(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("npm", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            # upgrade
            result = run_command("npm", "install", "-g", f"{name}@{version}", check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("npm", "install", "-g", f"{name}@{version}", check=False)
        if result.returncode == 0:
            if "up to date" in result.stdout.lower() or "added" not in result.stdout.lower():
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_vscode_extension(self, extension_id: str) -> InstallResult:
        result = run_command("code", "--install-extension", extension_id, check=False)
        if result.returncode == 0:
            return InstallResult(name=extension_id, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stdout.lower():
            return InstallResult(name=extension_id, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=extension_id, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_winget_package(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("winget", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            result = run_command("winget", "upgrade", "--id", name, "--source", "winget", "--accept-package-agreements", "--accept-source-agreements", check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("winget", "install", "--id", name, "--source", "winget", "--accept-package-agreements", "--accept-source-agreements", check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        if "already installed" in result.stdout.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_scoop_package(self, name: str, version: str, auto_confirm: bool = False) -> InstallResult:
        installed = self._get_installed_version("scoop", name)
        if installed:
            if installed == version.lstrip("="):
                return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Already installed v{installed}")
            if not auto_confirm:
                import typer
                action = typer.prompt(
                    f"  {name}: installed v{installed}, snapshot v{version}. Action",
                    type=typer.Choice(["skip", "upgrade"]),
                    default="skip",
                )
                if action == "skip":
                    return InstallResult(name=name, status=InstallStatus.SKIPPED, message=f"Kept v{installed}")
            result = run_command("scoop", "update", name, check=False)
            if result.returncode == 0:
                return InstallResult(name=name, status=InstallStatus.SUCCESS)
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

        result = run_command("scoop", "install", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def inject_env_var(self, key: str, value: str, config_file: str = "") -> InstallResult:
        from pathlib import Path
        from supersync.utils.platform import get_default_shell_config_file, is_windows

        if not config_file:
            config_file = get_default_shell_config_file()

        config_path = Path(config_file).expanduser()
        if not config_path.is_absolute():
            config_path = Path.home() / config_file

        # Choose injection syntax based on config file type
        if config_file.endswith(".ps1"):
            inject_line = f'$env:{key} = "{value}"\n'
            already_defined_check = f"$env:{key} ="
        else:
            inject_line = f'export {key}="{value}"\n'
            already_defined_check = f"export {key}="

        try:
            if config_path.exists():
                content = config_path.read_text()
                if already_defined_check in content:
                    return InstallResult(name=key, status=InstallStatus.SKIPPED, message="Already defined")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "a") as f:
                f.write(inject_line)

            return InstallResult(name=key, status=InstallStatus.SUCCESS)

        except Exception as e:
            return InstallResult(name=key, status=InstallStatus.FAILED, message=str(e))

    def deploy_dotfile(self, rel_path: str, content_b64: str, backup: bool = True, conflict_action: str = "backup") -> InstallResult:
        """Deploy a dotfile from base64-encoded content.

        Args:
            rel_path: Relative path from home directory.
            content_b64: Base64-encoded file content.
            backup: Whether to create backup of existing file.
            conflict_action: How to handle existing files - "backup", "skip", or "overwrite".
        """
        import base64
        from pathlib import Path

        target = Path.home() / rel_path

        try:
            if target.exists():
                if conflict_action == "skip":
                    return InstallResult(name=rel_path, status=InstallStatus.SKIPPED, message="Skipped (file exists)")
                if backup:
                    backup_path = Path(str(target) + ".supersync.bak")
                    backup_path.write_bytes(target.read_bytes())

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(content_b64))

            return InstallResult(name=rel_path, status=InstallStatus.SUCCESS)

        except Exception as e:
            return InstallResult(name=rel_path, status=InstallStatus.FAILED, message=str(e))
