import re
from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class ScoopScanner(ScannerBase):
    """Scans scoop for installed packages on Windows."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        scoop_check = run_command_optional("scoop", "--version")
        if scoop_check is None:
            return ScanResult(
                source="scoop",
                items=[],
                sensitive=[],
                errors=["scoop not found on this system"],
            )

        try:
            result = run_command("scoop", "list", check=False)
            if result.returncode != 0:
                errors.append(f"scoop list failed: {result.stderr.strip()}")
                return ScanResult(source="scoop", items=[], sensitive=[], errors=errors)

            lines = result.stdout.strip().split("\n")
            # scoop list output format:
            # Name    Version    Source Bucket
            # ----    -------    -----------
            # 7zip    23.01      main
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                # Skip header and separator lines
                if stripped.startswith("Name") or re.match(r'^[─\-]+', stripped):
                    continue

                parts = stripped.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    bucket = parts[2] if len(parts) >= 3 else ""
                else:
                    continue

                items.append(Item(
                    name=name,
                    version=version,
                    source="scoop",
                    extra={"bucket": bucket, "type": "scoop"},
                ))

        except Exception as e:
            errors.append(f"Failed to scan scoop: {e}")

        return ScanResult(source="scoop", items=items, sensitive=sensitive, errors=errors)
