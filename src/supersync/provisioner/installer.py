from dataclasses import dataclass
from enum import Enum

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

    def install_brew_formula(self, name: str, version: str) -> InstallResult:
        result = run_command("brew", "install", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stderr or "already installed" in result.stdout:
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_brew_cask(self, name: str, version: str) -> InstallResult:
        result = run_command("brew", "install", "--cask", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stderr or "already installed" in result.stdout:
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_pip_package(self, name: str, version: str) -> InstallResult:
        result = run_command("pip", "install", f"{name}=={version}", check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already satisfied" in result.stdout.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_npm_package(self, name: str, version: str) -> InstallResult:
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

    def inject_env_var(self, key: str, value: str, config_file: str = ".zshrc") -> InstallResult:
        from pathlib import Path

        config_path = Path(config_file).expanduser()
        if not config_path.is_absolute():
            config_path = Path.home() / config_file

        export_line = f'export {key}="{value}"\n'

        try:
            if config_path.exists():
                content = config_path.read_text()
                if f"export {key}=" in content:
                    return InstallResult(name=key, status=InstallStatus.SKIPPED, message="Already defined")

            with open(config_path, "a") as f:
                f.write(export_line)

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
