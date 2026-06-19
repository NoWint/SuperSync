from unittest.mock import patch
from supersync.scanner.dotfiles import DotfilesScanner
from supersync.scanner.base import ScanResult
from supersync.utils.platform import is_windows


def test_dotfiles_scan_reads_existing_files(tmp_path):
    scanner = DotfilesScanner()

    # Create files that exist on both platforms
    (tmp_path / ".gitconfig").write_text("[user]\n  name = Test\n")

    if is_windows():
        ps_dir = tmp_path / "Documents" / "PowerShell"
        ps_dir.mkdir(parents=True)
        (ps_dir / "Microsoft.PowerShell_profile.ps1").write_text("$env:TEST = 'hello'\n")
    else:
        (tmp_path / ".zshrc").write_text("alias ll='ls -la'\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "dotfiles"
    assert any(item.name == ".gitconfig" for item in result.items)


def test_dotfiles_scan_marks_ssh_as_sensitive(tmp_path):
    scanner = DotfilesScanner()

    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "config").write_text("Host github.com\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "config" and item.sensitive for item in result.sensitive)
