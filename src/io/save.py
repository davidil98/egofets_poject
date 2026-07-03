"""I/O utilities: SaveConfig, save_figure, record_script, save_result."""

import inspect
import io
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

# Re-export AnalysisResult for convenience imports
try:
    from ..analysis import AnalysisResult
except ImportError:
    AnalysisResult = None  # type: ignore


@dataclass
class SaveConfig:
    """Configuration for saving plots, data, and code.

    Attributes
    ----------
    enabled : bool
        Master switch. If False, no save operations are performed.
    output_dir : Path
        Base output directory. Subdirs are created automatically:
        - `<output_dir>/figures/` for images
        - `<output_dir>/scripts/` for generated code
        - `<project>/data/processed/` for CSV data
    basename : str
        Filename base (no extension). If empty, auto-generated
        from the measurement name and plot type.
    formats : list[str]
        Image formats to save. Any of: 'png', 'pdf', 'svg', 'jpg'.
    save_data : bool
        Also save a CSV of the data plotted.
    save_code : bool
        Also save the script that produced the figure (requires
        `record_script()` context manager or explicit `code=`).
    save_latex : bool
        Also save a LaTeX `\begin{figure}...` snippet.
    dpi : int
        Resolution for raster formats.
    overwrite : bool
        If False, skip files that already exist.
    """

    enabled: bool = False
    output_dir: Path = field(default_factory=lambda: Path("output"))
    basename: str = ""
    formats: list[str] = field(default_factory=lambda: ["png"])
    save_data: bool = True
    save_code: bool = True
    save_latex: bool = False
    dpi: int = 300
    overwrite: bool = False

    def fig_dir(self) -> Path:
        return self.output_dir / "figures"

    def script_dir(self) -> Path:
        return self.output_dir / "scripts"

    def data_dir(self, project_root: Path | None = None) -> Path:
        """CSV data goes to `<project_root>/data/processed/`."""
        if project_root is None:
            project_root = Path.cwd()
        while project_root != project_root.parent:
            if (project_root / "data").is_dir():
                return project_root / "data" / "processed"
            project_root = project_root.parent
        return Path.cwd() / "data" / "processed"


def auto_basename(parts: dict[str, Any]) -> str:
    """Build a filename base from a dict of identifying info.

    Skips None/empty values. Joins with '_'.

    Example:
        auto_basename({"name": "Batch3_Dispositivo1_Transfer_01",
                       "plot": "transfer", "axis": "log",
                       "vds": -0.8})
        → "Batch3_Dispositivo1_Transfer_01_transfer_log_vds-0.80"
    """
    pieces = []
    for k in ("name", "plot", "axis", "vds", "vgs", "tag"):
        v = parts.get(k)
        if v is None or v == "":
            continue
        if k in ("vds", "vgs") and isinstance(v, (int, float)):
            pieces.append(f"{k}{v:.2f}")
        else:
            pieces.append(str(v))
    if not pieces:
        pieces = ["figure"]
    return "_".join(pieces).replace(" ", "")


def _ensure_unique(path: Path, overwrite: bool) -> Path:
    """Return a unique path; respect overwrite flag."""
    if overwrite or not path.exists():
        return path
    stem, suf = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem}_{i}{suf}")
        if not candidate.exists():
            return candidate
        i += 1


def _latex_snippet(basename: str, caption: str, formats: list[str]) -> str:
    """Build a ready-to-paste LaTeX figure snippet."""
    primary = next((f for f in formats if f in ("pdf", "png", "svg")), "png")
    return (
        "\\begin{figure}[htbp]\n"
        "    \\centering\n"
        f"    \\includegraphics[width=0.85\\linewidth]{{{basename}.{primary}}}\n"
        f"    \\caption{{{caption or basename}}}\n"
        f"    \\label{{fig:{basename}}}\n"
        "\\end{figure}\n"
    )


# ── record_script context manager ─────────────────────────────────────

@contextmanager
def record_script() -> Iterator[list[str]]:
    """Capture the source of the `with` block by introspecting the caller.

    Usage:
        with record_script() as script_lines:
            fig, ax = plot_transfer(m, save=SAVE)
            save_result(result, save=SAVE)
        # script_lines contains the lines inside the with block

    Implementation: reads the caller's source via `inspect.getsource`,
    finds the line of the `with` statement, and includes all lines
    after it (up to the next top-level statement in the caller).
    More reliable than `sys.settrace`/`sys.monitoring` line tracing,
    which has limitations in Python 3.13+ and Jupyter.

    Note: works in regular Python scripts and Jupyter (the caller's
    frame is identified by walking the stack). In a REPL or after
    `exec()`, the source may be unavailable — pass the code
    explicitly via the `code=` argument of `save_figure`/`save_result`
    in that case.
    """
    import inspect

    captured: list[str] = []
    caller_frame = inspect.currentframe().f_back
    if caller_frame is None:
        yield captured
        return

    # Walk up the stack past the contextmanager internals to find the
    # user's frame (the one calling `with record_script()`).
    user_frame = caller_frame
    while user_frame is not None:
        fcode = user_frame.f_code
        # Skip our own frames and contextlib internals
        if "contextlib" in fcode.co_filename or "src/io/" in fcode.co_filename:
            user_frame = user_frame.f_back
            continue
        # Skip frames whose name is the contextmanager internals
        if fcode.co_name in ("__enter__", "__exit__", "contextmanager", "record_script"):
            user_frame = user_frame.f_back
            continue
        break

    if user_frame is None:
        yield captured
        return

    start_lineno = user_frame.f_lineno

    try:
        src = inspect.getsource(user_frame.f_code)
        lines = src.splitlines()
        # start_lineno is 1-indexed; lines is 0-indexed
        # Also account for the function's first lineno
        offset = user_frame.f_code.co_firstlineno
        idx = start_lineno - offset
        if 0 <= idx < len(lines):
            # Take all lines from the with statement onwards
            captured.extend(lines[idx:])
    except (OSError, TypeError):
        pass

    yield captured


# ── save_figure ───────────────────────────────────────────────────────

def save_figure(
    fig,
    save: SaveConfig,
    basename: str | None = None,
    data: pd.DataFrame | None = None,
    code: str | None = None,
    caption: str = "",
) -> list[Path]:
    """Save a matplotlib figure plus optional data, code, and LaTeX snippet.

    Returns the list of paths actually written.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save.
    save : SaveConfig
        Save configuration.
    basename : str | None
        Filename base. Falls back to `save.basename` then auto.
    data : pd.DataFrame | None
        Optional DataFrame to save as CSV alongside the figure.
    code : str | None
        Optional Python source to save as a .py file.
    caption : str
        Caption used in the LaTeX snippet (if save_latex=True).
    """
    if not save.enabled:
        return []

    base = basename or save.basename or auto_basename({"name": "figure"})
    written: list[Path] = []

    # ── images ──
    fig_dir = save.fig_dir()
    fig_dir.mkdir(parents=True, exist_ok=True)
    for fmt in save.formats:
        path = fig_dir / f"{base}.{fmt}"
        path = _ensure_unique(path, save.overwrite)
        if path.suffix in (".png", ".jpg", ".jpeg"):
            fig.savefig(path, dpi=save.dpi, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        written.append(path)

    # ── data ──
    if save.save_data and data is not None and not data.empty:
        data_dir = save.data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / f"{base}.csv"
        path = _ensure_unique(path, save.overwrite)
        data.to_csv(path, index=False)
        written.append(path)

    # ── code ──
    if save.save_code and code:
        script_dir = save.script_dir()
        script_dir.mkdir(parents=True, exist_ok=True)
        path = script_dir / f"{base}.py"
        path = _ensure_unique(path, save.overwrite)
        path.write_text(code)
        written.append(path)

    # ── latex ──
    if save.save_latex:
        fig_dir.mkdir(parents=True, exist_ok=True)
        path = fig_dir / f"{base}.tex"
        path = _ensure_unique(path, save.overwrite)
        path.write_text(_latex_snippet(base, caption, save.formats))
        written.append(path)

    return written


def save_result(
    result: "AnalysisResult",
    save: SaveConfig,
    basename: str | None = None,
    code: str | None = None,
) -> list[Path]:
    """Save an AnalysisResult: figure (if any), metrics JSON, data CSV."""
    if not save.enabled:
        return []
    written: list[Path] = []
    base = basename or save.basename or auto_basename(
        {"name": result.params.get("name", "result"), "plot": result.method}
    )

    # Figure
    if result.figure is not None:
        written += save_figure(
            result.figure, save, basename=base, code=code, caption=result.method
        )

    # Metrics as JSON
    if save.save_data:
        import json
        data_dir = save.data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / f"{base}_metrics.json"
        path = _ensure_unique(path, save.overwrite)
        path.write_text(json.dumps(result.metrics, indent=2, default=str))
        written.append(path)

    # Fit data
    if save.save_data and result.data is not None and not result.data.empty:
        data_dir = save.data_dir()
        path = data_dir / f"{base}_fit_data.csv"
        path = _ensure_unique(path, save.overwrite)
        result.data.to_csv(path, index=False)
        written.append(path)

    return written
