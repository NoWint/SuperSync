from supersync.manifest.schema import Manifest, BrewPackage, EnvVar, Dotfile, VscodeConfig
from supersync.provisioner.engine import ProvisionerEngine, RestoreReport, CategoryReport


def test_engine_generates_steps_from_manifest():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test",
        packages={
            "brew": [BrewPackage(name="git", version="2.45.0", package_type="formula")],
        },
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[Dotfile(path=".zshrc", content="abc", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )

    engine = ProvisionerEngine(manifest, dry_run=True)
    steps = engine._generate_steps()

    assert len(steps) > 0
    assert steps[0].type.value < steps[-1].type.value


def test_engine_dry_run_does_not_install():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test",
        packages={
            "brew": [BrewPackage(name="git", version="2.45.0", package_type="formula")],
        },
        env_vars=[],
        dotfiles=[],
        ide={},
    )

    engine = ProvisionerEngine(manifest, dry_run=True)

    from unittest.mock import patch
    with patch("supersync.provisioner.installer.Installer.install_brew_formula") as mock_install:
        report = engine.run()
        mock_install.assert_not_called()

    assert isinstance(report, RestoreReport)
