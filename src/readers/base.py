"""Abstract base class for instrument readers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..readers_core import Measurement


class Reader(ABC):
    """Base class for all instrument data readers.

    Subclasses must define `name` and implement `read()`.
    Optionally, override `can_read()` to autodetect if the reader
    can handle a given file.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def read(self, filepath: Path) -> dict[str, Measurement]:
        """Read the file and return a dict of {measurement_name: Measurement}."""
        ...

    def can_read(self, filepath: Path) -> bool:
        """Optional: detect if this reader can handle the file.

        Default: check that the file exists and has a supported extension.
        Subclasses can override for content-based detection.
        """
        if not filepath.exists():
            return False
        return filepath.suffix.lower() in {".hdf5", ".h5", ".he5"}

    def __repr__(self) -> str:
        return f"<Reader '{self.name}'>"
