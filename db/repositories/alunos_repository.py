"""Repository inicial de alunos."""

from __future__ import annotations

import pandas as pd


def dataframe_from_rows(rows) -> pd.DataFrame:
    return pd.DataFrame(rows or [])
