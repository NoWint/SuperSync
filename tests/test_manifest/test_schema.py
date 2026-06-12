from supersync.manifest.schema import (
    BrewPackage,
    PipPackage,
    NpmPackage,
    EnvVar,
    Dotfile,
    VscodeConfig,
    Manifest,
)


def test_brew_package():
    pkg = BrewPackage(name="git", version="2.45.0", package_type="formula")
    assert pkg.name == "git"
    assert pkg.package_type == "formula"


def test_manifest_creation():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={},
        env_vars=[],
        dotfiles=[],
        ide={},
    )
    assert manifest.version == "1.0"
    assert manifest.platform == "macos"


def test_manifest_serialization_roundtrip():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={
            "brew": [BrewPackage(name="git", version="2.45.0", package_type="formula")],
        },
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[Dotfile(path=".zshrc", content="abc123", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )
    data = manifest.model_dump()
    restored = Manifest.model_validate(data)
    assert restored.version == manifest.version
    assert len(restored.env_vars) == 1
