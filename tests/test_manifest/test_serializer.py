from supersync.manifest.schema import Manifest, EnvVar
from supersync.manifest.serializer import serialize_manifest, deserialize_manifest


def test_serialize_deserialize_roundtrip():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={},
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[],
        ide={},
    )

    yaml_str = serialize_manifest(manifest)
    assert isinstance(yaml_str, str)
    assert "FOO" in yaml_str

    restored = deserialize_manifest(yaml_str)
    assert restored.version == manifest.version
    assert len(restored.env_vars) == 1
    assert restored.env_vars[0].key == "FOO"
