from unittest.mock import patch, MagicMock
from supersync.scanner.npm import NpmScanner
from supersync.scanner.base import ScanResult


def test_npm_scan_parses_global_packages():
    scanner = NpmScanner()

    mock_result = MagicMock()
    mock_result.stdout = '{"dependencies":{"typescript":{"version":"5.5.0"},"eslint":{"version":"9.0.0"}}}'

    with patch("supersync.scanner.npm.run_command", return_value=mock_result):
        with patch("supersync.scanner.npm.run_command_optional", return_value=MagicMock(stdout="10.0.0")):
            with patch("pathlib.Path.exists", return_value=False):
                result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "npm"
    assert len(result.items) == 2
    assert result.items[0].name == "typescript"


def test_npm_scan_handles_npm_not_found():
    scanner = NpmScanner()

    with patch("supersync.scanner.npm.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "npm"
    assert len(result.items) == 0
    assert len(result.errors) == 1
