"""Table and LaTeX export helpers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Callable, Optional

import numpy as np
import pandas as pd


def ensure_output_dirs(root: Path) -> None:
    for path in [
        root / "outputs" / "tables",
        root / "outputs" / "figures",
        root / "outputs" / "logs",
        root / "paper_sections",
        root / "notebooks",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def format_for_paper(value: object) -> object:
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return ""
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:,.3f}"
    return value


def paper_table(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(format_for_paper)


def write_table(
    df: pd.DataFrame,
    csv_path: Path,
    tex_path: Optional[Path] = None,
    *,
    caption: Optional[str] = None,
    label: Optional[str] = None,
    formatter: Optional[Callable[[object], object]] = None,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    if tex_path is None:
        return
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    display_df = df.applymap(formatter or format_for_paper)
    latex = display_df.to_latex(
        index=False,
        escape=True,
        caption=caption,
        label=label,
        longtable=False,
        bold_rows=False,
    )
    latex = re.sub(
        r"(\\begin\{tabular\}\{[^}]+\})",
        r"\\resizebox{\\textwidth}{!}{%\n\1",
        latex,
        count=1,
    )
    latex = latex.replace(r"\end{tabular}", r"\end{tabular}%" + "\n}", 1)
    tex_path.write_text(latex, encoding="utf-8")


def write_markdown(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")
