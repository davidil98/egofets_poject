"""Standardized plotting for EGOFET measurements.

All plot functions accept an optional `save: SaveConfig` argument. When
`save.enabled=True`, the figure (and optionally data/code/LaTeX) is
written to disk via `save_figure()`.
"""

import re

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from .readers_core import Measurement
from .io import SaveConfig, auto_basename, save_figure
from .analysis import _split_monotonic_segments


def _curve_short(curve_name) -> str:
    """Convert 'curve_000' -> '0'. Returns '0' if name is missing."""
    if curve_name is None:
        return "0"
    m = re.search(r"(\d+)$", str(curve_name))
    return m.group(1) if m else str(curve_name)

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.figsize": (7, 5),
    }
)

TICKER = ticker.EngFormatter(unit="A")


def format_current_axis(ax):
    ax.yaxis.set_major_formatter(TICKER)


_AXIS_LABELS = {False: "linear", True: "log"}


def _curve_data_for_save(
    m: Measurement, mode: str, log: bool, sqrt: bool
) -> pd.DataFrame:
    """Extract the per-curve data used for plotting, for CSV saving."""
    df = m.data.copy()
    return df


def plot_transfer(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    log: bool = False,
    sqrt: bool = False,
    cmap: str = "viridis",
    curves: list[str] | None = None,
    save: SaveConfig | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot Id vs Vgs at fixed Vds (transfer curve).

    Each monotonic segment of every (V_DS, curve) sweep is drawn as its
    own continuous line, so forward and reverse sweeps no longer get
    concatenated into a single zig-zag that looks like a filled region.

    Parameters
    ----------
    cmap:
        Colormap used to assign one distinct base color per (V_DS, curve)
        pair; forward/reverse segments of the same pair share that color.
    curves:
        Optional list of curve identifiers (e.g. ``["curve_000", "curve_001"]``)
        to plot. ``None`` plots every curve present in the measurement.

    Returns (fig, ax). If `save` is provided and enabled, also saves
    the figure, data, code, and LaTeX snippet according to config.
    """
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    df = m.data
    vds_vals = sorted(df["V_DS"].dropna().unique())

    if "curve" in df.columns:
        curve_names = sorted(df["curve"].dropna().unique().tolist())
    else:
        curve_names = [None]
    if curves is not None:
        curve_names = [c for c in curve_names if c in curves]

    pairs = [(vds, c) for vds in vds_vals for c in curve_names]
    n_pairs = max(len(pairs), 1)
    cmap_obj = plt.get_cmap(cmap)
    if len(pairs) > 1:
        base_colors = [cmap_obj(i / (len(pairs) - 1)) for i in range(len(pairs))]
    else:
        base_colors = [cmap_obj(0.5)]

    for (vds, curve_name), base_color in zip(pairs, base_colors):
        sub = df[(df["V_DS"] == vds) & (df["curve"] == curve_name)]
        if sub.empty:
            continue
        # Use the original acquisition order so the segment splitter can
        # detect direction changes in V_GS.
        x_raw = sub["V_GS"].values
        if sqrt:
            y_raw = np.sqrt(np.abs(sub["I_DS"].values))
        elif log:
            y_raw = np.abs(sub["I_DS"].values)
        else:
            y_raw = sub["I_DS"].values

        segments = _split_monotonic_segments(x_raw)
        sweep = _curve_short(curve_name)
        for seg_i, (start, end, direction) in enumerate(segments):
            if end - start < 2:
                continue
            label = (
                f"V_DS = {vds:.2f} V, sweep {sweep} {direction}"
                if len(segments) > 1
                else f"V_DS = {vds:.2f} V, sweep {sweep}"
            )
            ax.plot(
                x_raw[start:end],
                y_raw[start:end],
                "o-",
                ms=3,
                color=base_color,
                label=label,
            )

    ax.set_xlabel("V_GS (V)")
    if sqrt:
        ax.set_ylabel("sqrt(|I_DS|) (A¹ᐟ²)")
    elif log:
        ax.set_ylabel("|I_DS| (A)")
        ax.set_yscale("log")
    else:
        ax.set_ylabel("I_DS (A)")
        format_current_axis(ax)

    ax.grid(True, alpha=0.3)
    ax.legend(title=f"{m.name}")
    ax.set_title(f"Transfer — {m.batch} {m.device}")
    fig.tight_layout()

    if save and save.enabled:
        vds_high = vds_vals[-1] if vds_vals else None
        basename = save.basename or auto_basename(
            {
                "name": m.name,
                "plot": "transfer",
                "axis": "sqrt" if sqrt else _AXIS_LABELS[log],
                "vds": vds_high,
            }
        )
        save_figure(fig, save, basename=basename, data=df)

    return fig, ax


def plot_output(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    cmap: str = "viridis",
    curves: list[str] | None = None,
    save: SaveConfig | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot Id vs Vds at fixed Vgs (output curve).

    Each monotonic segment of every (V_GS, curve) sweep is drawn as its
    own continuous line, so forward and reverse sweeps no longer get
    concatenated into a single zig-zag that looks like a filled region.
    """
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    df = m.data
    vgs_vals = sorted(df["V_GS"].dropna().unique())

    if "curve" in df.columns:
        curve_names = sorted(df["curve"].dropna().unique().tolist())
    else:
        curve_names = [None]
    if curves is not None:
        curve_names = [c for c in curve_names if c in curves]

    pairs = [(vgs, c) for vgs in vgs_vals for c in curve_names]
    n_pairs = max(len(pairs), 1)
    cmap_obj = plt.get_cmap(cmap)
    if len(pairs) > 1:
        base_colors = [cmap_obj(i / (len(pairs) - 1)) for i in range(len(pairs))]
    else:
        base_colors = [cmap_obj(0.5)]

    for (vgs, curve_name), base_color in zip(pairs, base_colors):
        sub = df[(df["V_GS"] == vgs) & (df["curve"] == curve_name)]
        if sub.empty:
            continue
        x_raw = sub["V_DS"].values
        y_raw = sub["I_DS"].values

        segments = _split_monotonic_segments(x_raw)
        sweep = _curve_short(curve_name)
        for start, end, direction in segments:
            if end - start < 2:
                continue
            label = (
                f"V_GS = {vgs:.2f} V, sweep {sweep} {direction}"
                if len(segments) > 1
                else f"V_GS = {vgs:.2f} V, sweep {sweep}"
            )
            ax.plot(
                x_raw[start:end],
                y_raw[start:end],
                "o-",
                ms=3,
                color=base_color,
                label=label,
            )

    ax.set_xlabel("V_DS (V)")
    ax.set_ylabel("I_DS (A)")
    format_current_axis(ax)
    ax.grid(True, alpha=0.3)
    ax.legend(title=f"{m.name}")
    ax.set_title(f"Output — {m.batch} {m.device}")
    fig.tight_layout()

    if save and save.enabled:
        vgs_low = vgs_vals[0] if vgs_vals else None
        basename = save.basename or auto_basename(
            {"name": m.name, "plot": "output", "vgs": vgs_low}
        )
        save_figure(fig, save, basename=basename, data=df)

    return fig, ax


def plot_stability(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    y_col: str = "I_DS",
    save: SaveConfig | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot a time-series measurement (stability / chronoamperometry)."""
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    df = m.data
    if "time" in df.columns:
        x = df["time"].values
        xlabel = "Time (s)"
    else:
        x = np.arange(len(df))
        xlabel = "Point index"

    ax.plot(x, df[y_col].values)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(y_col)
    format_current_axis(ax)
    ax.grid(True, alpha=0.3)
    ax.set_title(f"Stability — {m.name}")
    fig.tight_layout()

    if save and save.enabled:
        basename = save.basename or auto_basename(
            {"name": m.name, "plot": "stability", "axis": y_col}
        )
        save_figure(fig, save, basename=basename, data=df)

    return fig, ax


def plot_transfer_multi(
    measurements: dict[str, Measurement],
    mode: str = "transfer",
    *,
    log: bool = True,
    sqrt: bool = False,
    ncols: int = 2,
    figsize: tuple | None = None,
    cmap: str = "viridis",
    curves: list[str] | None = None,
    save: SaveConfig | None = None,
) -> tuple[plt.Figure, np.ndarray]:
    """Plot all measurements of a given mode in a grid."""
    selected = {name: m for name, m in measurements.items() if m.mode == mode}
    n = len(selected)
    nrows = int(np.ceil(n / ncols))
    if figsize is None:
        figsize = (6 * ncols, 4 * nrows)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)

    for i, (name, m) in enumerate(sorted(selected.items())):
        ax = axes[i // ncols][i % ncols]
        plot_transfer(m, ax=ax, log=log, sqrt=sqrt, cmap=cmap, curves=curves)
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)
    fig.tight_layout()

    if save and save.enabled:
        basename = save.basename or auto_basename(
            {"plot": f"all_{mode}", "axis": "sqrt" if sqrt else _AXIS_LABELS[log]}
        )
        # Save combined data: all measurements concatenated with a name column
        all_data = []
        for name, m in selected.items():
            d = m.data.copy()
            d["measurement"] = name
            all_data.append(d)
        combined = pd.concat(all_data, ignore_index=True) if all_data else None
        save_figure(fig, save, basename=basename, data=combined)

    return fig, axes


def plot_output_multi(
    measurements: dict[str, Measurement],
    *,
    ncols: int = 2,
    figsize: tuple | None = None,
    cmap: str = "viridis",
    curves: list[str] | None = None,
    save: SaveConfig | None = None,
) -> tuple[plt.Figure, np.ndarray]:
    """Plot all output measurements in a grid."""
    selected = {name: m for name, m in measurements.items() if m.mode == "output"}
    n = len(selected)
    nrows = int(np.ceil(n / ncols))
    if figsize is None:
        figsize = (6 * ncols, 4 * nrows)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)

    for i, (name, m) in enumerate(sorted(selected.items())):
        ax = axes[i // ncols][i % ncols]
        plot_output(m, ax=ax, cmap=cmap, curves=curves)
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)
    fig.tight_layout()

    if save and save.enabled:
        basename = save.basename or auto_basename({"plot": "all_output"})
        all_data = []
        for name, m in selected.items():
            d = m.data.copy()
            d["measurement"] = name
            all_data.append(d)
        combined = pd.concat(all_data, ignore_index=True) if all_data else None
        save_figure(fig, save, basename=basename, data=combined)

    return fig, axes
