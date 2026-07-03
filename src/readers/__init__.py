"""Reader package — register and select instrument readers.

Public API:
    - `Reader` (base class)         → from src.readers.base
    - `Measurement` (dataclass)     → re-exported here
    - `read_hdf5(filepath, reader)`  → convenience function
    - `register_reader(r)`          → for new instruments
    - `get_reader(name)`            → lookup by name
    - `list_readers()`              → all registered names
"""

from .base import Reader
from .keithley2600 import Keithley2600Reader
from ..readers_core import Measurement, list_measurements

# Registry functions defined after base classes to avoid circular imports
from . import registry as _registry
from .registry import register_reader, get_reader, list_readers, read_hdf5

__all__ = [
    "Reader",
    "Keithley2600Reader",
    "Measurement",
    "list_measurements",
    "read_hdf5",
    "register_reader",
    "get_reader",
    "list_readers",
]
