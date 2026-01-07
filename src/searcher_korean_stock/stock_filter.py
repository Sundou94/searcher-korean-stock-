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

    # 필수 조건: 거래량 (완화됨)
    cond_amount = (df['amount'] >= 2 * df['amount_avg20']) | (df['amount_rank_pct'] >= 0.8)

    # 캔들 형태 (더 유연하게)
    cond_candle = (
        (df['close'] > df['open'])
        & (df['body_ratio'] >= 0.5)  # 0.7 -> 0.5
        & (df['close'] >= df['high'] * 0.95)  # 0.97 -> 0.95
        & (df['upper_wick_ratio'] <= 0.25)  # 0.15 -> 0.25
        & (df['lower_wick_ratio'] <= 0.25)  # 0.15 -> 0.25
    )

    # 상승 추세 (OR 조건으로 더 많이 선택)
    cond_trend = (
        (df['close'] >= df['high_max20'] * 0.99)  # 상위 1%
        | (
            (df['ma5'] > df['ma10'])
            & (df['ma10'] > df['ma20'])
            & (df['low'] <= df['ma5'] * 1.05)  # 1.02 -> 1.05
            & (df['close'] >= df['ma5'] * 0.98)  # >= -> >= 0.98
        )
        | ((df['close'] > df['ma20']) & (df['ma5'] > df['ma20']))  # 추가 조건
    )

    # 변동성 (낮춤)
    cond_volatility = df['range_avg10'] >= 0.02  # 0.03 -> 0.02

    # 오후 거래 (완화)
    cond_afternoon = (
        (df['after_13_amount'] >= df['amount'] * 0.3)  # 0.4 -> 0.3
        | (df['after_13_low'] >= df['low'] * 0.98)  # >= -> >= 0.98
    )

    # 전일 변화율 (범위 확대)
    cond_day_change = (df['prev_change'] >= 0.005) & (df['prev_change'] <= 0.1)  # 0.01~0.06 -> 0.005~0.1

    # 시가총액 및 주가 (범위 확대)
    cond_spec = (
        ((df['market_cap'] >= 1e11) | (df['market_cap'].isna()))  # 최소값 낮춤
        & ((df['market_cap'] <= 1e12) | (df['market_cap'].isna()))  # 최대값 올림
        & (df['close'] >= 1000)  # 5000 -> 1000
    )

    # 제외 조건 (완화)
    exclude_limit_up = (df['close'] >= df['high'] * 0.999) & (df['prev_change'] > 0.3)  # 0.25 -> 0.3
    exclude_long_wick = (df['upper_wick_ratio'] > 0.5) | (df['lower_wick_ratio'] > 0.5)  # 0.35 -> 0.5
    exclude_recent_big_drop = df.groupby('ticker')['prev_change'].transform(lambda x: x.rolling(5).min()) <= -0.08  # -0.05 -> -0.08
    exclude_volume_decline = df['vol_ma5'] < df['vol_ma5_prev'] * 0.5  # 완화: 50% 이상 감소만 제외

    candidates = df[
        (cond_amount | cond_candle | cond_trend)  # AND에서 OR로 변경: 하나라도 만족하면 OK
        & cond_volatility
        & (cond_afternoon | df['after_13_amount'].isna())  # 오후 데이터 없으면 제외 안 함
        & (cond_day_change | df['prev_change'].isna())  # 이전 데이터 없으면 제외 안 함
        & (cond_spec | df['market_cap'].isna())  # 시가총액 없으면 제외 안 함
        & (~exclude_limit_up)
        & (~exclude_long_wick)
        & (~exclude_recent_big_drop)
        & (~exclude_volume_decline | df['vol_ma5_prev'].isna())  # 과거 거래량 없으면 제외 안 함
    ].copy()

    return candidates
