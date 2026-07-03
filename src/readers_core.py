"""Measurement dataclass (shared by all readers)."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Measurement:
    name: str
    mode: str  # "transfer", "output", "stability"
    batch: str = ""
    device: str = ""
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: dict = field(default_factory=dict)
    curves: list = field(default_factory=list)

    def __repr__(self):
        n = len(self.data)
        return f"Measurement({self.name!r}, mode={self.mode!r}, {n} points)"


def list_measurements(measurements: dict[str, Measurement]) -> pd.DataFrame:
    """Return a summary DataFrame of all measurements."""
    rows = []
    for name, m in measurements.items():
        rows.append(
            {
                "name": name,
                "mode": m.mode,
                "batch": m.batch,
                "device": m.device,
                "n_points": len(m.data),
                "columns": list(m.data.columns),
            }
        )
    return pd.DataFrame(rows)
