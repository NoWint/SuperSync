import json

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class BrewScanner(ScannerBase):
    """Scans Homebrew for installed formulae and casks."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        errors: list[str] = []

        brew_check = run_command_optional("brew", "--version")
        if brew_check is None:
            return ScanResult(
                source="brew",
                items=[],
                sensitive=[],
                errors=["Homebrew not found on this system"],
            )

        try:
            info_result = run_command("brew", "info", "--json=v2", "--installed")
            info_data = json.loads(info_result.stdout)

            for formula in info_data.get("formulae", []):
                name = formula["name"]
                versions = formula.get("installed", [])
                version = versions[0]["version"] if versions else "unknown"
                items.append(Item(name=name, version=version, source="brew", extra={"type": "formula"}))

            for cask in info_data.get("casks", []):
                name = cask["name"]
                version = cask.get("version", "unknown")
                items.append(Item(name=name, version=version, source="brew", extra={"type": "cask"}))

        except Exception as e:
            errors.append(f"Failed to scan Homebrew: {e}")

        return ScanResult(source="brew", items=items, sensitive=[], errors=errors)
