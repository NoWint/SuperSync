from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class StepType(IntEnum):
    BREW_FORMULA = 10
    BREW_CASK = 11
    PIP_PACKAGE = 20
    NPM_PACKAGE = 21
    ENV_VAR = 30
    DOTFILE = 40
    IDE_EXTENSION = 50
    VSCODE_SETTINGS = 51


@dataclass
class Step:
    type: StepType
    name: str
    source: str
    version: Optional[str] = None
    content: Optional[str] = None
    path: Optional[str] = None
    sensitive: bool = False
    encrypted: bool = False
    extra: dict = field(default_factory=dict)


def topological_sort(steps: list[Step]) -> list[Step]:
    """Sort steps by dependency order."""
    return sorted(steps, key=lambda s: s.type.value)
