"""Reader registry and convenience functions."""

from pathlib import Path
from typing import TYPE_CHECKING, Type

from .base import Reader

if TYPE_CHECKING:
    from ..readers_core import Measurement

_READERS: dict[str, Reader] = {}


def register_reader(reader: Reader | Type[Reader]) -> None:
    """Register a reader instance or class."""
    if isinstance(reader, type):
        reader = reader()
    if not reader.name:
        raise ValueError("Reader must have a non-empty 'name' attribute")
    _READERS[reader.name] = reader


def get_reader(name: str) -> Reader:
    """Get a registered reader by name."""
    if name not in _READERS:
        raise KeyError(
            f"Reader '{name}' not registered. "
            f"Available: {list(_READERS.keys())}"
        )
    return _READERS[name]


def list_readers() -> list[str]:
    """List names of all registered readers."""
    return list(_READERS.keys())


def read_hdf5(
    filepath: str | Path,
    reader: str | None = None,
) -> "dict[str, Measurement]":
    """Read an HDF5 file using the named reader (or autodetect).

    Parameters
    ----------
    filepath : str | Path
        Path to the HDF5 file.
    reader : str | None
        Name of a registered reader. If None, autodetects by trying
        each registered reader's `can_read()` in order.

    Returns
    -------
    dict[str, Measurement]
        Dict mapping measurement names to Measurement objects.
    """
    filepath = Path(filepath)

    if reader is None:
        for r in _READERS.values():
            if r.can_read(filepath):
                return r.read(filepath)
        raise ValueError(f"No registered reader can handle {filepath}")
    return get_reader(reader).read(filepath)


# Auto-register built-in readers
from .keithley2600 import Keithley2600Reader  # noqa: E402

register_reader(Keithley2600Reader)
