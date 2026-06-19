import subprocess
from unittest.mock import patch, MagicMock

from supersync.scanner.winget import WingetScanner
from supersync.scanner.base import ScanResult


def test_winget_not_available():
    """When winget is not found, scanner should return empty result with error."""
    with patch("supersync.scanner.winget.run_command_optional", return_value=None):
        scanner = WingetScanner()
        result = scanner.scan()
        assert result.source == "winget"
        assert len(result.items) == 0
        assert len(result.errors) == 1
        assert "winget not found" in result.errors[0]


def test_winget_scan_parses_output():
    """WingetScanner should parse winget list output correctly."""
    mock_output = MagicMock()
    mock_output.returncode = 0
    mock_output.stdout = """Name                           Id                           Version
-------------------------------------------------------------->
Visual Studio Code              Microsoft.VisualStudioCode    1.90.0
Python                          Python.Python.3.12           3.12.4
GitHub CLI                      GitHub.cli                   2.95.0
"""

    with patch("supersync.scanner.winget.run_command_optional", return_value=MagicMock(returncode=0)):
        with patch("supersync.scanner.winget.run_command", return_value=mock_output):
            scanner = WingetScanner()
            result = scanner.scan()
            assert result.source == "winget"
            assert len(result.items) == 3
            assert result.items[0].name == "Microsoft.VisualStudioCode"
            assert result.items[0].version == "1.90.0"
            assert result.items[1].name == "Python.Python.3.12"
            assert result.items[1].version == "3.12.4"


def test_winget_scan_handles_failure():
    """WingetScanner should handle winget list failure gracefully."""
    mock_output = MagicMock()
    mock_output.returncode = 1
    mock_output.stderr = "No packages found"

    with patch("supersync.scanner.winget.run_command_optional", return_value=MagicMock(returncode=0)):
        with patch("supersync.scanner.winget.run_command", return_value=mock_output):
            scanner = WingetScanner()
            result = scanner.scan()
            assert result.source == "winget"
            assert len(result.items) == 0
            assert len(result.errors) == 1
