"""I/O submodule: figure and data saving utilities."""

from .save import (
    AnalysisResult,
    SaveConfig,
    auto_basename,
    record_script,
    save_figure,
    save_result,
)

__all__ = [
    "AnalysisResult",
    "SaveConfig",
    "auto_basename",
    "record_script",
    "save_figure",
    "save_result",
]
