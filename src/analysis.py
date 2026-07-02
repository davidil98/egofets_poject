"""Parameter extraction for EGOFET measurements: Vth, mobility, SS, on/off ratio."""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .readers import Measurement


def _linear(x: np.ndarray, a: float, b: float) -> np.ndarray:
    return a * x + b


def extract_vth_linear(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
) -> dict:
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].unique()
        vds = max(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])

    if vgs_range is not None:
        v_min, v_max = vgs_range
        df = df[(df["V_GS"] >= v_min) & (df["V_GS"] <= v_max)]

    x = df["V_GS"].values
    y = df["I_DS"].values

    popt, _ = curve_fit(_linear, x, y)
    a, b = popt

    vth = -b / a if a != 0 else np.nan

    y_fit = _linear(x, *popt)
    r_squared = 1 - np.sum((y - y_fit) ** 2) / np.sum((y - np.mean(y)) ** 2)

    return {
        "method": "linear_extrapolation",
        "V_DS": vds,
        "Vth": vth,
        "slope": a,
        "intercept": b,
        "R²": r_squared,
        "fit_points": len(x),
        "popts": popt,
    }


def extract_vth_sqrt(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
) -> dict:
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].unique()
        vds = max(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])

    if vgs_range is not None:
        v_min, v_max = vgs_range
        df = df[(df["V_GS"] >= v_min) & (df["V_GS"] <= v_max)]

    x = df["V_GS"].values
    y = np.sqrt(np.abs(df["I_DS"].values))

    popt, _ = curve_fit(_linear, x, y)
    a, b = popt

    vth = -b / a if a != 0 else np.nan

    y_fit = _linear(x, *popt)
    r_squared = 1 - np.sum((y - y_fit) ** 2) / np.sum((y - np.mean(y)) ** 2)

    return {
        "method": "sqrt_Id_extrapolation",
        "V_DS": vds,
        "Vth": vth,
        "slope": a,
        "intercept": b,
        "R²": r_squared,
        "fit_points": len(x),
        "popts": popt,
    }


def extract_mobility(
    m: Measurement,
    vth: float,
    vds: float | None = None,
    *,
    w: float = 1e-3,
    l: float = 1e-4,
    ci: float = 1e-4,
) -> float:
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].unique()
        vds = max(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

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
    return mu


def extract_ss(
    m: Measurement,
    vds: float | None = None,
    *,
    vgs_range: tuple[float, float] | None = None,
) -> float:
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].unique()
        vds = min(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

    df = df.sort_values("V_GS").dropna(subset=["V_GS", "I_DS"])

    if vgs_range is not None:
        v_min, v_max = vgs_range
        df = df[(df["V_GS"] >= v_min) & (df["V_GS"] <= v_max)]

    log_id = np.log10(np.abs(df["I_DS"].values))
    vgs = df["V_GS"].values

    d_log_id = np.diff(log_id)
    d_vgs = np.diff(vgs)
    ss_values = d_vgs / d_log_id

    return np.nanmean(ss_values)


def extract_on_off_ratio(
    m: Measurement,
    vds: float | None = None,
) -> dict:
    df = m.data.copy()
    if vds is not None:
        df = df[df["V_DS"] == vds]
    elif "V_DS" in df.columns:
        vds_vals = df["V_DS"].unique()
        vds = max(vds_vals, key=abs)
        df = df[df["V_DS"] == vds]

    abs_id = np.abs(df["I_DS"].values)
    i_on = abs_id.max()
    i_off = abs_id.min()

    if i_off == 0:
        nonzero = abs_id[abs_id != 0]
        i_off = nonzero.min() if len(nonzero) > 0 else np.nan

    on_off = i_on / i_off if i_off != 0 else np.inf

    return {
        "I_on": i_on,
        "I_off": i_off,
        "on_off_ratio": on_off,
        "log_on_off": np.log10(on_off) if on_off != np.inf else np.inf,
    }
