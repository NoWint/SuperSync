import base64
import re
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional

VSCODE_SETTINGS_PATH = "Library/Application Support/Code/User/settings.json"

SENSITIVE_SETTINGS_PATTERNS = re.compile(
    r"(token|secret|key|password|credential|auth)",
    re.IGNORECASE,
)


class IdeScanner(ScannerBase):
    """Scans IDE configurations (VS Code extensions and settings)."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        code_check = run_command_optional("code", "--version")
        if code_check is None:
            return ScanResult(
                source="ide",
                items=[],
                sensitive=[],
                errors=["VS Code CLI not found (code command unavailable)"],
            )

        try:
            ext_result = run_command("code", "--list-extensions")
            extensions = [line.strip() for line in ext_result.stdout.strip().split("\n") if line.strip()]

            for ext_id in extensions:
                items.append(Item(
                    name=ext_id,
                    source="ide",
                    extra={"ide": "vscode", "type": "extension"},
                ))

        except Exception as e:
            errors.append(f"Failed to scan VS Code extensions: {e}")

        settings_path = Path.home() / VSCODE_SETTINGS_PATH
        if settings_path.exists():
            try:
                content = base64.b64encode(settings_path.read_bytes()).decode("ascii")
                raw_content = settings_path.read_text()

                is_sensitive = bool(SENSITIVE_SETTINGS_PATTERNS.search(raw_content))

                item = Item(
                    name="settings.json",
                    path=VSCODE_SETTINGS_PATH,
                    content=content,
                    source="ide",
                    sensitive=is_sensitive,
                    extra={"ide": "vscode", "type": "settings"},
                )

                if is_sensitive:
                    sensitive.append(item)
                else:
                    items.append(item)

            except Exception as e:
                errors.append(f"Failed to read VS Code settings: {e}")

        return ScanResult(source="ide", items=items, sensitive=sensitive, errors=errors)
