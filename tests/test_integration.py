"""Integration test: scan → encrypt → decrypt → restore (dry-run) roundtrip."""

from supersync.manifest.schema import (
    Manifest,
    BrewPackage,
    PipPackage,
    NpmPackage,
    EnvVar,
    Dotfile,
    VscodeConfig,
)
from supersync.manifest.serializer import serialize_manifest, deserialize_manifest
from supersync.manifest.crypto import encrypt_data, decrypt_data
from supersync.provisioner.engine import ProvisionerEngine


def test_full_roundtrip():
    """Test the complete scan → serialize → encrypt → decrypt → restore flow."""

    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={
            "brew": [
                BrewPackage(name="git", version="2.45.0", package_type="formula"),
                BrewPackage(name="visual-studio-code", version="1.90.0", package_type="cask"),
            ],
            "pip": [PipPackage(name="requests", version="2.32.0")],
            "npm": [NpmPackage(name="typescript", version="5.5.0")],
        },
        env_vars=[EnvVar(key="PYTHONPATH", value="/usr/local/lib/python3")],
        dotfiles=[Dotfile(path=".zshrc", content="YWxpYXMgbGw9J2xzIC1sYScK", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )

    # Serialize to YAML
    yaml_str = serialize_manifest(manifest)
    assert isinstance(yaml_str, str)
    assert "git" in yaml_str

    # Encrypt
    password = "test-integration-password"
    encrypted = encrypt_data(yaml_str.encode("utf-8"), password)
    assert encrypted[:4] == b"SSNC"

    # Decrypt
    decrypted_data = decrypt_data(encrypted, password)
    decrypted_yaml = decrypted_data.decode("utf-8")

    # Deserialize
    restored_manifest = deserialize_manifest(decrypted_yaml)
    assert restored_manifest.version == "1.0"
    assert len(restored_manifest.packages["brew"]) == 2
    assert len(restored_manifest.packages["pip"]) == 1
    assert len(restored_manifest.env_vars) == 1
    assert len(restored_manifest.dotfiles) == 1
    assert len(restored_manifest.ide["vscode"].extensions) == 1

    # Restore (dry-run)
    engine = ProvisionerEngine(restored_manifest, dry_run=True)
    report = engine.run()

    assert report.total > 0
    assert report.total_success > 0


def test_encrypt_decrypt_with_wrong_password():
    """Verify that wrong password raises an error."""
    data = b"test data"
    password = "correct"

    encrypted = encrypt_data(data, password)

    import pytest
    with pytest.raises(Exception):
        decrypt_data(encrypted, "wrong")
