import yaml

from supersync.manifest.schema import Manifest


def serialize_manifest(manifest: Manifest) -> str:
    """Serialize a Manifest to YAML string."""
    data = manifest.model_dump(mode="json")
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def deserialize_manifest(yaml_str: str) -> Manifest:
    """Deserialize a YAML string to a Manifest."""
    data = yaml.safe_load(yaml_str)
    return Manifest.model_validate(data)
