from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.sort_values(['ticker', 'date'], inplace=True)

    grouped = df.groupby('ticker')
    df['ma5'] = grouped['close'].transform(lambda x: x.rolling(5).mean())
    df['ma10'] = grouped['close'].transform(lambda x: x.rolling(10).mean())
    df['ma20'] = grouped['close'].transform(lambda x: x.rolling(20).mean())
    df['amount_avg20'] = grouped['amount'].transform(lambda x: x.rolling(20).mean())
    df['range_pct'] = (df['high'] - df['low']) / df['close']
    df['range_avg10'] = grouped['range_pct'].transform(lambda x: x.rolling(10).mean())
    df['high_max20'] = grouped['high'].transform(lambda x: x.rolling(20).max())

    # daily change vs previous close
    prev_close = grouped['close'].shift(1)
    df['prev_change'] = (df['close'] - prev_close) / prev_close

    # volume trend detection
    df['vol_ma5'] = grouped['volume'].transform(lambda x: x.rolling(5).mean())
    df['vol_ma5_prev'] = df.groupby('ticker')['vol_ma5'].shift(5)

    # percentile rank of amount per day
    df['amount_rank_pct'] = df.groupby('date')['amount'].rank(pct=True, method='max')

    # wick lengths
    body = (df['close'] - df['open']).abs()
    span = (df['high'] - df['low']).replace(0, np.nan)
    df['body_ratio'] = body / span
    df['upper_wick_ratio'] = (df['high'] - df['close']) / span
    df['lower_wick_ratio'] = (df['open'] - df['low']) / span

    return df


def filter_candidates(df: pd.DataFrame) -> pd.DataFrame:
    df = _compute_indicators(df)

    cond_amount = (df['amount'] >= 3 * df['amount_avg20']) & (df['amount_rank_pct'] >= 0.9)

    cond_candle = (
        (df['close'] > df['open'])
        & (df['body_ratio'] >= 0.7)
        & (df['close'] >= df['high'] * 0.97)
        & (df['upper_wick_ratio'] <= 0.15)
        & (df['lower_wick_ratio'] <= 0.15)
    )

    cond_trend = (
        (df['close'] >= df['high_max20'])
        | (
            (df['ma5'] > df['ma10'])
            & (df['ma10'] > df['ma20'])
            & (df['low'] <= df['ma5'] * 1.02)
            & (df['close'] >= df['ma5'])
        )
    )

    cond_volatility = df['range_avg10'] >= 0.03

    cond_afternoon = (
        (df['after_13_amount'] >= df['amount'] * 0.4)
        & (df['after_13_low'] >= df['low'])
    )

    cond_day_change = (df['prev_change'] >= 0.01) & (df['prev_change'] <= 0.06)

    cond_spec = (
        (df['market_cap'] >= 2e11) & (df['market_cap'] <= 8e11) & (df['close'] >= 5000) & (df['close'] <= 40000)
    )

    # exclusion conditions
    exclude_limit_up = (df['close'] >= df['high'] * 0.999) & (df['prev_change'] > 0.25)
    exclude_long_wick = (df['upper_wick_ratio'] > 0.35) | (df['lower_wick_ratio'] > 0.35)
    exclude_recent_big_drop = df.groupby('ticker')['prev_change'].transform(lambda x: x.rolling(5).min()) <= -0.05
    exclude_volume_decline = df['vol_ma5'] < df['vol_ma5_prev']

    candidates = df[
        cond_amount
        & cond_candle
        & cond_trend
        & cond_volatility
        & cond_afternoon
        & cond_day_change
        & cond_spec
        & (~exclude_limit_up)
        & (~exclude_long_wick)
        & (~exclude_recent_big_drop)
        & (~exclude_volume_decline)
    ].copy()

    return candidates
