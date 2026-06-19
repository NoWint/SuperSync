import base64
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.platform import get_dotfiles_paths, is_windows

SSH_DIR = ".ssh"
SSH_FILES = ["config", "known_hosts"]


class DotfilesScanner(ScannerBase):
    """Scans dotfiles and SSH config files."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        home = Path.home()
        dotfiles_paths = get_dotfiles_paths()

        for rel_path in dotfiles_paths:
            file_path = home / rel_path
            if not file_path.exists():
                continue

            try:
                content = base64.b64encode(file_path.read_bytes()).decode("ascii")
                items.append(Item(
                    name=file_path.name,
                    path=rel_path,
                    content=content,
                    source="dotfiles",
                    sensitive=False,
                ))
            except Exception as e:
                errors.append(f"Failed to read {rel_path}: {e}")

        ssh_dir = home / SSH_DIR
        if ssh_dir.exists():
            for ssh_file in SSH_FILES:
                ssh_path = ssh_dir / ssh_file
                if not ssh_path.exists():
                    continue

                try:
                    content = base64.b64encode(ssh_path.read_bytes()).decode("ascii")
                    sensitive.append(Item(
                        name=ssh_file,
                        path=f"{SSH_DIR}/{ssh_file}",
                        content=content,
                        source="dotfiles",
                        sensitive=True,
                    ))
                except Exception as e:
                    errors.append(f"Failed to read {SSH_DIR}/{ssh_file}: {e}")

        return ScanResult(source="dotfiles", items=items, sensitive=sensitive, errors=errors)
