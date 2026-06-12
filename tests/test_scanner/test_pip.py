from unittest.mock import patch, MagicMock
from supersync.scanner.pip_scanner import PipScanner
from supersync.scanner.base import ScanResult


def test_pip_scan_parses_packages():
    scanner = PipScanner()

    mock_result = MagicMock()
    mock_result.stdout = '[{"name":"requests","version":"2.32.0"},{"name":"flask","version":"3.0.0"}]'

    with patch("supersync.scanner.pip_scanner.run_command", return_value=mock_result):
        with patch("supersync.scanner.pip_scanner.run_command_optional", return_value=MagicMock(stdout="pip 24.0")):
            result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "pip"
    assert len(result.items) == 2
    assert result.items[0].name == "requests"
    assert result.items[0].version == "2.32.0"


def test_pip_scan_handles_pip_not_found():
    scanner = PipScanner()

    with patch("supersync.scanner.pip_scanner.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "pip"
    assert len(result.items) == 0
    assert len(result.errors) == 1
