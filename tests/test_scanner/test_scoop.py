from unittest.mock import patch, MagicMock

from supersync.scanner.scoop import ScoopScanner


def test_scoop_not_available():
    """When scoop is not found, scanner should return empty result with error."""
    with patch("supersync.scanner.scoop.run_command_optional", return_value=None):
        scanner = ScoopScanner()
        result = scanner.scan()
        assert result.source == "scoop"
        assert len(result.items) == 0
        assert len(result.errors) == 1
        assert "scoop not found" in result.errors[0]


def test_scoop_scan_parses_output():
    """ScoopScanner should parse scoop list output correctly."""
    mock_output = MagicMock()
    mock_output.returncode = 0
    mock_output.stdout = """Name    Version    Source Bucket
----    -------    -----------
7zip    23.01      main
git     2.54.0     main
nodejs  22.3.0     main
"""

    with patch("supersync.scanner.scoop.run_command_optional", return_value=MagicMock(returncode=0)):
        with patch("supersync.scanner.scoop.run_command", return_value=mock_output):
            scanner = ScoopScanner()
            result = scanner.scan()
            assert result.source == "scoop"
            assert len(result.items) == 3
            assert result.items[0].name == "7zip"
            assert result.items[0].version == "23.01"
            assert result.items[0].extra["bucket"] == "main"
            assert result.items[1].name == "git"
            assert result.items[1].version == "2.54.0"


def test_scoop_scan_handles_failure():
    """ScoopScanner should handle scoop list failure gracefully."""
    mock_output = MagicMock()
    mock_output.returncode = 1
    mock_output.stderr = "scoop command failed"

    with patch("supersync.scanner.scoop.run_command_optional", return_value=MagicMock(returncode=0)):
        with patch("supersync.scanner.scoop.run_command", return_value=mock_output):
            scanner = ScoopScanner()
            result = scanner.scan()
            assert result.source == "scoop"
            assert len(result.items) == 0
            assert len(result.errors) == 1
