from __future__ import annotations

import pandas as pd

from .stock_filter import filter_candidates
from .scorer import score_candidates


def select_candidates(df: pd.DataFrame, limit: int = 4) -> pd.DataFrame:
    filtered = filter_candidates(df)
    scored = score_candidates(filtered)
    top = scored.groupby('date').head(limit)
    return top
