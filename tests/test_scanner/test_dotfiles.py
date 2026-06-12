from unittest.mock import patch
from supersync.scanner.dotfiles import DotfilesScanner
from supersync.scanner.base import ScanResult


def test_dotfiles_scan_reads_existing_files(tmp_path):
    scanner = DotfilesScanner()

    (tmp_path / ".zshrc").write_text("alias ll='ls -la'\n")
    (tmp_path / ".gitconfig").write_text("[user]\n  name = Test\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "dotfiles"
    assert any(item.name == ".zshrc" for item in result.items)
    assert any(item.name == ".gitconfig" for item in result.items)


def test_dotfiles_scan_marks_ssh_as_sensitive(tmp_path):
    scanner = DotfilesScanner()

    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "config").write_text("Host github.com\n")
    (tmp_path / ".zshrc").write_text("alias ll='ls -la'\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "config" and item.sensitive for item in result.sensitive)
