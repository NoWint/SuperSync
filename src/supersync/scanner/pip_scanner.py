import json

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class PipScanner(ScannerBase):
    """Scans pip for globally installed packages."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        errors: list[str] = []

        pip_check = run_command_optional("pip", "--version")
        if pip_check is None:
            return ScanResult(
                source="pip",
                items=[],
                sensitive=[],
                errors=["pip not found on this system"],
            )

        try:
            result = run_command("pip", "list", "--format=json")
            packages = json.loads(result.stdout)

            for pkg in packages:
                items.append(Item(
                    name=pkg["name"],
                    version=pkg["version"],
                    source="pip",
                ))

        except Exception as e:
            errors.append(f"Failed to scan pip: {e}")

        return ScanResult(source="pip", items=items, sensitive=[], errors=errors)
