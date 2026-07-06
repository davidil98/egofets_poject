"""Reader package for EGOFET measurement files.

HDF5 file structure:
    /                          (root)
      MeasurementName/         (group, attrs: measurement_mode)
        curve_000/             (group, attrs: V_DS o V_GS)
          measured_V_GS        (dataset)
          measured_I_DS        (dataset)
        curve_001/
          ...
"""

from .base import print_structure
from .keithley_dean import list_measurements, read_curve, read_all_curves

__all__ = [
    "print_structure",
    "list_measurements",
    "read_curve",
    "read_all_curves",
]
