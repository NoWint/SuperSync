from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    """A single scanned item (package, file, env var, etc.)."""
    name: str
    source: str
    version: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    sensitive: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class ScanResult:
    """Result from a single scanner."""
    source: str
    items: list[Item]
    sensitive: list[Item]
    errors: list[str]


class ScannerBase(ABC):
    """Base class for all environment scanners."""

    @abstractmethod
    def scan(self) -> ScanResult:
        """Scan the environment and return results."""
        ...
