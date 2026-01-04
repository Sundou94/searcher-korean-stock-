from __future__ import annotations

import pandas as pd


def score_candidates(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()

    scored['score_amount'] = (scored['amount'] / scored['amount_avg20']).clip(0, 10)
    scored['score_close_to_high'] = scored['close'] / scored['high']
    scored['score_volatility'] = (scored['range_avg10'] / 0.03).clip(0, 2)
    scored['score_ma'] = ((scored['ma5'] > scored['ma10']) & (scored['ma10'] > scored['ma20'])).astype(float)

    scored['total_score'] = (
        scored['score_amount'] * 0.4 + scored['score_close_to_high'] * 0.25 + scored['score_volatility'] * 0.2 + scored['score_ma'] * 0.15
    )

    scored.sort_values(['date', 'total_score'], ascending=[True, False], inplace=True)
    return scored
