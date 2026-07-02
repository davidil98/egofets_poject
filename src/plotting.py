"""Standardized plotting for EGOFET measurements."""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from .readers import Measurement

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


def plot_transfer(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    log: bool = False,
    sqrt: bool = False,
    cmap: str = "viridis",
    label_fmt: str = "V_DS = {V_DS:.2f} V",
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots()

    df = m.data
    vds_vals = sorted(df["V_DS"].dropna().unique())

    for vds in vds_vals:
        subset = df[df["V_DS"] == vds].sort_values("V_GS")
        x = subset["V_GS"].values
        if sqrt:
            y = np.sqrt(np.abs(subset["I_DS"].values))
        elif log:
            y = np.abs(subset["I_DS"].values)
        else:
            y = subset["I_DS"].values
        ax.plot(x, y, "o-", ms=3, label=label_fmt.format(V_DS=vds))

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
    return ax


def plot_output(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    cmap: str = "viridis",
    label_fmt: str = "V_GS = {V_GS:.2f} V",
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots()

    df = m.data
    vgs_vals = sorted(df["V_GS"].dropna().unique())

    for vgs in vgs_vals:
        subset = df[df["V_GS"] == vgs].sort_values("V_DS")
        x = subset["V_DS"].values
        y = subset["I_DS"].values
        ax.plot(x, y, "o-", ms=3, label=label_fmt.format(V_GS=vgs))

    ax.set_xlabel("V_DS (V)")
    ax.set_ylabel("I_DS (A)")
    format_current_axis(ax)
    ax.grid(True, alpha=0.3)
    ax.legend(title=f"{m.name}")
    ax.set_title(f"Output — {m.batch} {m.device}")
    return ax


def plot_stability(
    m: Measurement,
    ax: plt.Axes | None = None,
    *,
    y_col: str = "I_DS",
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots()

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
    return ax


def plot_transfer_multi(
    measurements: dict[str, Measurement],
    mode: str = "transfer",
    *,
    log: bool = True,
    sqrt: bool = False,
    ncols: int = 2,
    figsize: tuple | None = None,
) -> tuple[plt.Figure, list[plt.Axes]]:
    transfer_ms = {
        name: m
        for name, m in measurements.items()
        if m.mode == mode
    }

    n = len(transfer_ms)
    nrows = int(np.ceil(n / ncols))
    if figsize is None:
        figsize = (6 * ncols, 4 * nrows)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)

    for i, (name, m) in enumerate(sorted(transfer_ms.items())):
        ax = axes[i // ncols][i % ncols]
        plot_transfer(m, ax=ax, log=log, sqrt=sqrt)

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.tight_layout()
    return fig, axes


def plot_output_multi(
    measurements: dict[str, Measurement],
    *,
    ncols: int = 2,
    figsize: tuple | None = None,
) -> tuple[plt.Figure, list[plt.Axes]]:
    return plot_transfer_multi(
        measurements, mode="output", log=False, ncols=ncols, figsize=figsize
    )
