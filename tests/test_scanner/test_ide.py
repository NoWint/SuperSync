from unittest.mock import patch, MagicMock
from supersync.scanner.ide import IdeScanner
from supersync.scanner.base import ScanResult


def test_ide_scan_parses_vscode_extensions():
    scanner = IdeScanner()

    mock_result = MagicMock()
    mock_result.stdout = "ms-python.python\nesbenp.prettier-vscode\n"

    with patch("supersync.scanner.ide.run_command", return_value=mock_result):
        with patch("supersync.scanner.ide.run_command_optional", return_value=mock_result):
            with patch("pathlib.Path.exists", return_value=False):
                result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "ide"
    assert len(result.items) == 2
    assert result.items[0].name == "ms-python.python"


def test_ide_scan_handles_vscode_not_found():
    scanner = IdeScanner()

    with patch("supersync.scanner.ide.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "ide"
    assert len(result.items) == 0
    assert len(result.errors) == 1
