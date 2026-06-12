from unittest.mock import patch, MagicMock
from supersync.scanner.brew import BrewScanner
from supersync.scanner.base import ScanResult


def test_brew_scan_parses_formula_and_cask():
    scanner = BrewScanner()

    mock_info_output = MagicMock()
    mock_info_output.stdout = '{"formulae":[{"name":"git","installed":[{"version":"2.45.0"}]},{"name":"node","installed":[{"version":"22.2.0"}]}],"casks":[]}'

    with patch("supersync.scanner.brew.run_command", return_value=mock_info_output):
        with patch("supersync.scanner.brew.run_command_optional", return_value=MagicMock(stdout="Homebrew 4.0")):
            result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "brew"
    assert len(result.items) > 0
    assert any(item.name == "git" for item in result.items)


def test_brew_scan_handles_brew_not_found():
    scanner = BrewScanner()

    with patch("supersync.scanner.brew.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "brew"
    assert len(result.items) == 0
    assert len(result.errors) == 1
