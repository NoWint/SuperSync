import json
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class NpmScanner(ScannerBase):
    """Scans npm for globally installed packages and .npmrc tokens."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        npm_check = run_command_optional("npm", "--version")
        if npm_check is None:
            return ScanResult(
                source="npm",
                items=[],
                sensitive=[],
                errors=["npm not found on this system"],
            )

        try:
            result = run_command("npm", "list", "-g", "--json")
            data = json.loads(result.stdout)

            for name, info in data.get("dependencies", {}).items():
                version = info.get("version", "unknown")
                items.append(Item(
                    name=name,
                    version=version,
                    source="npm",
                    extra={"global": True},
                ))

        except Exception as e:
            errors.append(f"Failed to scan npm: {e}")

        npmrc_path = Path.home() / ".npmrc"
        if npmrc_path.exists():
            try:
                content = npmrc_path.read_text()
                if "_authToken" in content or "_password" in content:
                    sensitive.append(Item(
                        name=".npmrc",
                        path=str(npmrc_path),
                        content=content,
                        source="npm",
                        sensitive=True,
                    ))
            except Exception:
                pass

        return ScanResult(source="npm", items=items, sensitive=sensitive, errors=errors)
