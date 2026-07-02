"""HDF5 reader for EGOFET measurement data."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
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


def _parse_measurement_name(name: str) -> dict[str, str]:
    parts = name.split("_", 1)
    batch_dev = parts[0] if len(parts) > 1 else ""
    info = {"batch": "", "device": ""}
    for part in batch_dev.replace("Dispositivo", "Dev").split("_"):
        if part.startswith("Batch"):
            info["batch"] = part
        elif part.startswith("Dev"):
            info["device"] = part
    return info


def _curve_to_dataframe(group: h5py.Group) -> pd.DataFrame:
    records = {}
    for ds_name in group.keys():
        data = group[ds_name][:]
        label = ds_name.replace("measured_", "").replace("calculated_", "")
        records[label] = data
    df = pd.DataFrame(records)
    for attr_name, attr_val in group.attrs.items():
        if attr_name not in ("measurement_counter", "timestamp"):
            df[attr_name] = attr_val
    return df


def read_hdf5(filepath: str | Path) -> dict[str, Measurement]:
    filepath = Path(filepath)
    measurements = {}

    with h5py.File(filepath, "r") as f:
        for top_name in f.keys():
            group = f[top_name]

            info = _parse_measurement_name(top_name)

            mode = group.attrs.get("measurement_mode", "")
            has_curves = any(
                isinstance(group[k], h5py.Group) and k.startswith("curve_")
                for k in group.keys()
            )

            if has_curves:
                dfs = []
                curves_info = []
                for curve_name in sorted(group.keys()):
                    if not curve_name.startswith("curve_"):
                        continue
                    cg = group[curve_name]
                    df = _curve_to_dataframe(cg)
                    df["curve"] = curve_name
                    df["timestamp"] = cg.attrs.get("timestamp", "")
                    dfs.append(df)

                    curve_info = {"name": curve_name}
                    for an, av in cg.attrs.items():
                        if an not in ("measurement_counter", "timestamp"):
                            curve_info[an] = av
                    curves_info.append(curve_info)

                full_df = pd.concat(dfs, ignore_index=True)
                timestamp = group.attrs.get("timestamp", "")

                metadata = {}
                for an, av in group.attrs.items():
                    if an not in ("measurement_mode", "timestamp", "description"):
                        metadata[an] = av

                m = Measurement(
                    name=top_name,
                    mode=mode,
                    batch=info["batch"],
                    device=info["device"],
                    data=full_df,
                    metadata=metadata,
                    curves=curves_info,
                )
            else:
                records = {}
                for ds_name in group.keys():
                    data = group[ds_name][:]
                    label = ds_name.replace("measured_", "")
                    records[label] = data
                df = pd.DataFrame(records)
                timestamp = group.attrs.get("timestamp", "")
                if "timestamp" not in df.columns and timestamp:
                    df["timestamp"] = timestamp

                metadata = {}
                for an, av in group.attrs.items():
                    if an not in ("timestamp", "description"):
                        metadata[an] = av

                m = Measurement(
                    name=top_name,
                    mode=mode if mode else "stability",
                    batch=info["batch"],
                    device=info["device"],
                    data=df,
                    metadata=metadata,
                )

            measurements[top_name] = m

    return measurements


def list_measurements(measurements: dict[str, Measurement]) -> pd.DataFrame:
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
