from unittest.mock import patch
from supersync.scanner.env_vars import EnvVarsScanner
from supersync.scanner.base import ScanResult


def test_env_vars_scan_extracts_exports(tmp_path):
    scanner = EnvVarsScanner()

    zshrc = tmp_path / ".zshrc"
    zshrc.write_text('export PYTHONPATH="/usr/local/lib/python3"\nexport JAVA_HOME="/Library/Java"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "env_vars"
    assert any(item.name == "PYTHONPATH" for item in result.items)


def test_env_vars_scan_detects_sensitive_vars(tmp_path):
    scanner = EnvVarsScanner()

    zshrc = tmp_path / ".zshrc"
    zshrc.write_text('export GITHUB_TOKEN="ghp_abc123"\nexport PYTHONPATH="/usr/local"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "GITHUB_TOKEN" and item.sensitive for item in result.sensitive)
