import os
import re
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.platform import get_shell_config_files, is_windows

SENSITIVE_PATTERNS = re.compile(
    r"(token|secret|key|password|credential|auth|api_key|private)",
    re.IGNORECASE,
)

EXPORT_PATTERN = re.compile(r'^export\s+(\w+)=(.+)$', re.MULTILINE)

# PowerShell env var patterns:
# $env:KEY = "VALUE"
# $env:KEY = 'VALUE'
# $env:KEY = VALUE
PS_ENV_PATTERN = re.compile(r'^\$env:(\w+)\s*=\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)


class EnvVarsScanner(ScannerBase):
    """Scans shell config files for exported environment variables."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        home = Path.home()
        config_files = get_shell_config_files()

        for config_file in config_files:
            config_path = home / config_file
            if not config_path.exists():
                continue

            try:
                content = config_path.read_text()

                # Choose pattern based on file type
                if config_file.endswith(".ps1"):
                    pattern = PS_ENV_PATTERN
                else:
                    pattern = EXPORT_PATTERN

                for match in pattern.finditer(content):
                    name = match.group(1)
                    value = match.group(2).strip().strip('"').strip("'")

                    item = Item(
                        name=name,
                        content=value,
                        source="env_vars",
                        sensitive=SENSITIVE_PATTERNS.search(name) is not None,
                        extra={"config_file": config_file},
                    )

                    if item.sensitive:
                        sensitive.append(item)
                    else:
                        items.append(item)

            except Exception as e:
                errors.append(f"Failed to read {config_file}: {e}")

        return ScanResult(source="env_vars", items=items, sensitive=sensitive, errors=errors)
