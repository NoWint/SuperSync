from unittest.mock import patch, MagicMock
from supersync.provisioner.installer import Installer, InstallResult, InstallStatus


def test_install_brew_formula():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_brew_formula("git", "2.45.0")

    assert result.status == InstallStatus.SUCCESS


def test_install_brew_formula_already_installed():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="already installed")
        result = installer.install_brew_formula("git", "2.45.0")

    assert result.status == InstallStatus.SKIPPED


def test_install_pip_package():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_pip_package("requests", "2.32.0")

    assert result.status == InstallStatus.SUCCESS


def test_install_vscode_extension():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_vscode_extension("ms-python.python")

    assert result.status == InstallStatus.SUCCESS
