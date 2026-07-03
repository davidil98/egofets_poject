"""Parameter extraction for EGOFET measurements: Vth, mobility, SS, on/off ratio.

Each extraction function returns an `AnalysisResult` dataclass containing
the method, parameters used, computed metrics, optional fit data, and
optional figure.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .readers_core import Measurement


@dataclass
class AnalysisResult:
    """Result of a parameter extraction routine.

    Attributes
    ----------
    method : str
        Name of the method (e.g. 'sqrt_Id_extrapolation').
    params : dict
        Input parameters used (V_DS, vgs_range, etc.).
    metrics : dict
        Computed metrics (Vth, R², slope, etc.).
    data : pd.DataFrame | None
        The data points used for the fit (with `fit` column added if
        applicable).
    figure : matplotlib.figure.Figure | None
        Optional figure showing the fit.
    notes : str
        Optional free-text notes.
    """

    method: str
    params: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    data: pd.DataFrame | None = None
    figure: Any = None
    notes: str = ""

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access for backward compatibility."""
        if key in self.metrics:
            return self.metrics[key]
        if key in self.params:
            return self.params[key]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in self.metrics or key in self.params

    def keys(self):
        return {**self.params, **self.metrics}.keys()

    def get(self, key: str, default=None):
        if key in self.metrics:
            return self.metrics[key]
        if key in self.params:
            return self.params[key]
        return default


def _linear(x: np.ndarray, a: float, b: float) -> np.ndarray:
    return a * x + b


def _split_monotonic_segments(x: np.ndarray) -> list[tuple[int, int, str]]:
    """Split an x-series into monotonic segments.

    Returns a list of ``(start_idx, end_idx, direction)`` tuples where
    ``direction`` is ``"fwd"`` (x increasing) or ``"rev"`` (x decreasing).
    Direction is assigned to the first segment; subsequent segments flip
    between fwd/rev each time the sign of the differences changes.
    """
    if len(x) < 2:
        return [(0, len(x), "fwd")] if len(x) else []

    signs = np.sign(np.diff(x))
    if np.all(signs == 0):
        return [(0, len(x), "fwd")]

    nonzero = signs[signs != 0]
    first_dir = "fwd" if nonzero[0] > 0 else "rev"
    direction = first_dir

    segments: list[tuple[int, int, str]] = []
    start = 0
    prev = first_dir
    for i in range(1, len(signs)):
        if signs[i] == 0:
            continue
        cur = "fwd" if signs[i] > 0 else "rev"
        if cur != prev:
            segments.append((start, i + 1, prev))
            start = i
            prev = cur
    segments.append((start, len(x), prev))
    return segments


def _select_vds(df: pd.DataFrame, vds: float | None) -> tuple[pd.DataFrame, float | None]:
    if vds is not None:
        return df[df["V_DS"] == vds], vds
    if "V_DS" in df.columns:
        vds_vals = df["V_DS"].dropna().unique()
        vds = max(vds_vals, key=abs)
        return df[df["V_DS"] == vds], vds
    return df, vds


def _r_squared(x: np.ndarray, y: np.ndarray, popt) -> float:
    y_fit = _linear(x, *popt)
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else np.nan


def extract_vth_linear(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
    name: str = "",
) -> AnalysisResult:
    """Linear extrapolation of Id vs Vgs to find threshold voltage.

    Best applied in the linear (triode) region.
    """
    df = m.data.copy()
    df, vds = _select_vds(df, vds)
    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])
    if vgs_range is not None:
        df = df[(df["V_GS"] >= vgs_range[0]) & (df["V_GS"] <= vgs_range[1])]

    x = df["V_GS"].values
    y = df["I_DS"].values

    popt, _ = curve_fit(_linear, x, y)
    a, b = popt
    vth = -b / a if a != 0 else np.nan
    r2 = _r_squared(x, y, popt)

    df_out = df.copy()
    df_out["fit"] = _linear(x, *popt)

    return AnalysisResult(
        method="vth_linear",
        params={"name": name or m.name, "V_DS": vds, "vgs_range": vgs_range},
        metrics={"Vth": vth, "slope": a, "intercept": b, "R²": r2, "fit_points": len(x)},
        data=df_out,
    )


def extract_vth_sqrt(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
    name: str = "",
) -> AnalysisResult:
    """sqrt(Id) extrapolation in the saturation region."""
    df = m.data.copy()
    df, vds = _select_vds(df, vds)
    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])
    if vgs_range is not None:
        df = df[(df["V_GS"] >= vgs_range[0]) & (df["V_GS"] <= vgs_range[1])]

    x = df["V_GS"].values
    y = np.sqrt(np.abs(df["I_DS"].values))

    popt, _ = curve_fit(_linear, x, y)
    a, b = popt
    vth = -b / a if a != 0 else np.nan
    r2 = _r_squared(x, y, popt)

    df_out = df.copy()
    df_out["fit_sqrt"] = _linear(x, *popt)

    return AnalysisResult(
        method="vth_sqrt",
        params={"name": name or m.name, "V_DS": vds, "vgs_range": vgs_range},
        metrics={"Vth": vth, "slope": a, "intercept": b, "R²": r2, "fit_points": len(x)},
        data=df_out,
    )


def extract_mobility(
    m: Measurement,
    vth: float,
    vds: float | None = None,
    *,
    w: float = 1e-3,
    l: float = 1e-4,
    ci: float = 1e-4,
    name: str = "",
) -> AnalysisResult:
    """Extract field-effect mobility from sqrt(Id) in saturation."""
    df = m.data.copy()
    df, vds = _select_vds(df, vds)
    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])

    x = df["V_GS"].values
    y_sqrt = np.sqrt(np.abs(df["I_DS"].values))

    mask = (x < vth) if x[-1] < x[0] else (x > vth)
    if not mask.any():
        mask = slice(None)
    a, b = np.polyfit(x[mask], y_sqrt[mask], 1)

    if vds is None:
        vds = abs(df["V_DS"].iloc[0])
    mu = 2 * a**2 * l / (w * ci * abs(vds))

    return AnalysisResult(
        method="mobility",
        params={"name": name or m.name, "V_DS": vds, "Vth": vth, "w": w, "l": l, "ci": ci},
        metrics={"mobility": mu, "slope_sqrt": a, "intercept_sqrt": b},
    )


def extract_ss(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
    name: str = "",
    min_points: int = 8,
) -> AnalysisResult:
    """Subthreshold swing (V/dec) from log(|Id|) vs Vgs.

    Each curve is split into its monotonic (forward/reverse) segments
    so that hysteresis data does not pollute the fit. For every segment
    we fit ``log10(|I_DS|) = a * V_GS + b`` and store ``SS = 1/|a|`` as
    the per-segment swing. The reported ``SS`` metric is the **minimum**
    across segments (the most ideal, i.e. steepest subthreshold slope).

    Parameters
    ----------
    vds:
        V_DS to use. If ``None``, the smallest-|V_DS| curve is used.
    vgs_range:
        Optional ``(vgs_lo, vgs_hi)`` to restrict the fit to a
        subthreshold window.
    min_points:
        Skip segments with fewer than this many points (after the
        ``vgs_range`` mask) to keep the linear fit meaningful.
    """
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].dropna().unique()
        vds = min(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

    df = df.dropna(subset=["V_GS", "I_DS"])

    has_curve = "curve" in df.columns
    if has_curve:
        curve_groups = list(df.groupby("curve", sort=False))
    else:
        curve_groups = [("curve_000", df)]

    per_segment: dict[str, dict[str, float]] = {}
    fit_rows: list[dict] = []
    total_used = 0

    for curve_name, cdf in curve_groups:
        cdf = cdf.reset_index(drop=True)
        vgs_full = cdf["V_GS"].values
        ids_full = cdf["I_DS"].values
        log_id_full = np.log10(np.abs(ids_full))

        for start, end, direction in _split_monotonic_segments(vgs_full):
            seg_len = end - start
            if seg_len < min_points:
                continue

            vgs_seg = vgs_full[start:end]
            log_id_seg = log_id_full[start:end]
            ids_seg = ids_full[start:end]

            if vgs_range is not None:
                mask = (vgs_seg >= vgs_range[0]) & (vgs_seg <= vgs_range[1])
                if mask.sum() < min_points:
                    continue
                vgs_fit = vgs_seg[mask]
                log_fit = log_id_seg[mask]
            else:
                vgs_fit = vgs_seg
                log_fit = log_id_seg

            slope, intercept = np.polyfit(vgs_fit, log_fit, 1)
            if slope == 0 or not np.isfinite(slope):
                continue
            ss_val = 1.0 / abs(slope)
            y_hat = slope * vgs_fit + intercept
            ss_res = np.sum((log_fit - y_hat) ** 2)
            ss_tot = np.sum((log_fit - np.mean(log_fit)) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot != 0 else float("nan")

            key = f"{curve_name} {direction}"
            per_segment[key] = {
                "SS": float(ss_val),
                "SS_mV_dec": float(ss_val * 1000),
                "slope_dlogI_dV": float(slope),
                "R²": float(r2),
                "n_points": int(len(vgs_fit)),
            }
            total_used += len(vgs_fit)

            if vgs_range is None:
                for j in range(len(vgs_fit)):
                    fit_rows.append(
                        {
                            "curve": curve_name,
                            "direction": direction,
                            "V_GS": float(vgs_fit[j]),
                            "log10_I": float(log_fit[j]),
                            "fit": float(y_hat[j]),
                            "I_DS": float(ids_seg[j]) if vgs_range is None else float("nan"),
                        }
                    )

    if not per_segment:
        empty = AnalysisResult(
            method="ss",
            params={"name": name or m.name, "V_DS": vds, "vgs_range": vgs_range},
            metrics={"SS": float("nan"), "SS_mV_dec": float("nan"), "n_points": 0},
            data=df,
            notes="No usable monotonic segment found for SS extraction.",
        )
        return empty

    ss_values = np.array([v["SS"] for v in per_segment.values()])
    best_ss = float(ss_values.min())
    best_segment = min(per_segment, key=lambda k: per_segment[k]["SS"])

    data_out: pd.DataFrame | None = None
    if fit_rows:
        data_out = pd.DataFrame(fit_rows)

    return AnalysisResult(
        method="ss",
        params={
            "name": name or m.name,
            "V_DS": vds,
            "vgs_range": vgs_range,
            "min_points": min_points,
        },
        metrics={
            "SS": best_ss,
            "SS_mV_dec": best_ss * 1000,
            "best_segment": best_segment,
            "segments": per_segment,
            "n_points": int(total_used),
        },
        data=data_out if data_out is not None else df,
    )


def extract_on_off_ratio(
    m: Measurement,
    vds: float | None = None,
    *,
    name: str = "",
) -> AnalysisResult:
    """On/off current ratio: max(|Id|) / min(|Id|)."""
    df = m.data.copy()
    df, vds = _select_vds(df, vds)
    abs_id = np.abs(df["I_DS"].values)
    i_on = float(abs_id.max())
    i_off = abs_id[abs_id != 0].min() if (abs_id == 0).any() else float(abs_id.min())
    on_off = i_on / i_off if i_off != 0 else np.inf

    return AnalysisResult(
        method="on_off",
        params={"name": name or m.name, "V_DS": vds},
        metrics={
            "I_on": i_on,
            "I_off": i_off,
            "on_off_ratio": on_off,
            "log_on_off": float(np.log10(on_off)) if on_off != np.inf else float("inf"),
        },
    )
