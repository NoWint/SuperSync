from unittest.mock import patch
from supersync.scanner.env_vars import EnvVarsScanner
from supersync.scanner.base import ScanResult
from supersync.utils.platform import is_windows


def test_env_vars_scan_extracts_exports(tmp_path):
    scanner = EnvVarsScanner()

    if is_windows():
        ps_dir = tmp_path / "Documents" / "PowerShell"
        ps_dir.mkdir(parents=True)
        (ps_dir / "Microsoft.PowerShell_profile.ps1").write_text(
            '$env:PYTHONPATH = "/usr/local/lib/python3"\n$env:JAVA_HOME = "/Library/Java"\n'
        )
    else:
        zshrc = tmp_path / ".zshrc"
        zshrc.write_text('export PYTHONPATH="/usr/local/lib/python3"\nexport JAVA_HOME="/Library/Java"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "env_vars"
    assert any(item.name == "PYTHONPATH" for item in result.items)


def test_env_vars_scan_detects_sensitive_vars(tmp_path):
    scanner = EnvVarsScanner()

    if is_windows():
        ps_dir = tmp_path / "Documents" / "PowerShell"
        ps_dir.mkdir(parents=True)
        (ps_dir / "Microsoft.PowerShell_profile.ps1").write_text(
            '$env:GITHUB_TOKEN = "ghp_abc123"\n$env:PYTHONPATH = "/usr/local"\n'
        )
    else:
        zshrc = tmp_path / ".zshrc"
        zshrc.write_text('export GITHUB_TOKEN="ghp_abc123"\nexport PYTHONPATH="/usr/local"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "GITHUB_TOKEN" and item.sensitive for item in result.sensitive)


def test_env_vars_scan_powershell_format(tmp_path):
    """Test PowerShell $env:KEY = "VALUE" parsing."""
    scanner = EnvVarsScanner()
    ps_dir = tmp_path / "Documents" / "PowerShell"
    ps_dir.mkdir(parents=True)
    (ps_dir / "Microsoft.PowerShell_profile.ps1").write_text(
        '$env:MY_VAR = "hello world"\n$env:ANOTHER = \'test\'\n'
    )

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "MY_VAR" for item in result.items)
    assert any(item.name == "ANOTHER" for item in result.items)
