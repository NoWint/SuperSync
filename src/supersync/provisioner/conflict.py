from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ConflictType(Enum):
    DOTFILE_EXISTS = "dotfile_exists"
    PACKAGE_VERSION_MISMATCH = "package_version_mismatch"


@dataclass
class Conflict:
    type: ConflictType
    name: str
    message: str
    details: dict = field(default_factory=dict)


class ConflictDetector:
    """Detects potential conflicts before restoration."""

    def detect_dotfile_conflicts(
        self, dotfiles: list[dict[str, Any]], home_dir: Path
    ) -> list[Conflict]:
        conflicts = []

        for dotfile in dotfiles:
            rel_path = dotfile.get("path", "")
            target_path = home_dir / rel_path

            if target_path.exists():
                conflicts.append(Conflict(
                    type=ConflictType.DOTFILE_EXISTS,
                    name=rel_path,
                    message=f"File already exists: {rel_path}",
                    details={"path": str(target_path)},
                ))

        return conflicts

    def detect_package_conflicts(
        self, packages: dict[str, list], installed_packages: dict[str, dict[str, str]]
    ) -> list[Conflict]:
        conflicts = []

        for manager, pkg_list in packages.items():
            installed = installed_packages.get(manager, {})
            for pkg in pkg_list:
                name = pkg.name if hasattr(pkg, "name") else pkg.get("name", "")
                version = pkg.version if hasattr(pkg, "version") else pkg.get("version", "")

                if name in installed and installed[name] != version:
                    conflicts.append(Conflict(
                        type=ConflictType.PACKAGE_VERSION_MISMATCH,
                        name=name,
                        message=f"Version mismatch for {name}: installed {installed[name]}, manifest {version}",
                        details={
                            "installed_version": installed[name],
                            "manifest_version": version,
                        },
                    ))

        return conflicts
