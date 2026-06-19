import re
from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class WingetScanner(ScannerBase):
    """Scans winget for installed packages on Windows."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        winget_check = run_command_optional("winget", "--version")
        if winget_check is None:
            return ScanResult(
                source="winget",
                items=[],
                sensitive=[],
                errors=["winget not found on this system"],
            )

        try:
            result = run_command("winget", "list", "--source", "winget", "--disable-interactivity", check=False)
            if result.returncode != 0:
                errors.append(f"winget list failed: {result.stderr.strip()}")
                return ScanResult(source="winget", items=[], sensitive=[], errors=errors)

            lines = result.stdout.strip().split("\n")
            # winget list output format:
            # Name    Id                    Version
            # ------  -------------------- ---------
            # App     Publisher.App          1.0.0
            # Skip header lines (first 2-3 lines)
            data_started = False
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                # Skip until we find the separator line (---)
                if re.match(r'^[─\-]+', stripped):
                    data_started = True
                    continue
                if not data_started:
                    continue

                # Parse the line - winget uses fixed-width columns
                # Try to extract Id and Version
                parts = stripped.split()
                if len(parts) >= 3:
                    # Last part is version, second-to-last is Id, rest is Name
                    version = parts[-1]
                    pkg_id = parts[-2]
                    name = " ".join(parts[:-2])
                elif len(parts) == 2:
                    name = parts[0]
                    pkg_id = parts[0]
                    version = parts[1]
                else:
                    continue

                # Skip entries without a proper version or with unknown version
                if version in ("Version", "—", "-", ""):
                    version = "unknown"

                items.append(Item(
                    name=pkg_id,
                    version=version,
                    source="winget",
                    extra={"display_name": name, "type": "winget"},
                ))

        except Exception as e:
            errors.append(f"Failed to scan winget: {e}")

        return ScanResult(source="winget", items=items, sensitive=sensitive, errors=errors)
