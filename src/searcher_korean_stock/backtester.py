from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .portfolio import Portfolio, TradeRecord
from .strategy import select_candidates


@dataclass
class BacktestResult:
    portfolio: Portfolio
    trade_log: pd.DataFrame
    selection_log: pd.DataFrame


def simulate(df: pd.DataFrame, initial_capital: float = 10_000_000) -> BacktestResult:
    """Run day-by-day backtest based on the next-day +2% target and -1.5% stop."""
    df = df.sort_values(['date', 'ticker']).copy()

    candidates = select_candidates(df)
    portfolio = Portfolio(initial_capital=initial_capital)

    trade_records: List[TradeRecord] = []
    selection_rows: List[Dict] = []

    dates = sorted(df['date'].unique())
    df_by_date = {d: day for d, day in df.groupby('date')}

    for i, date in enumerate(dates[:-1]):
        day_candidates = candidates[candidates['date'] == date]
        if day_candidates.empty:
            portfolio.update_equity(date, 0.0)
            continue

        next_day = dates[i + 1]
        next_data = df_by_date[next_day].set_index('ticker')
        n = min(len(day_candidates), 4)
        allocation = portfolio.allocate(n)

        for _, row in day_candidates.head(4).iterrows():
            ticker = row['ticker']
            buy_price = row['close']
            target = buy_price * 1.02
            stop = buy_price * 0.985

            if ticker not in next_data.index:
                continue

            nhigh = next_data.loc[ticker, 'high']
            nlow = next_data.loc[ticker, 'low']
            nclose = next_data.loc[ticker, 'close']

            if nhigh >= target:
                sell_price = target
                result = 'win'
            elif nlow <= stop:
                sell_price = stop
                result = 'loss'
            else:
                sell_price = nclose
                result = 'hold_exit'

            ret = (sell_price - buy_price) / buy_price
            pnl = allocation * ret
            portfolio.update_equity(next_day, pnl)

            record = TradeRecord(
                date=date,
                ticker=ticker,
                buy_price=buy_price,
                sell_price=sell_price,
                return_pct=ret,
                result=result,
            )
            portfolio.log_trade(record)
            selection_rows.append({
                'date': date,
                'ticker': ticker,
                'score': row['total_score'],
                'allocation': allocation,
                'target': target,
                'stop': stop,
            })

    trade_log = portfolio.to_frame()
    selection_log = pd.DataFrame(selection_rows)
    return BacktestResult(portfolio=portfolio, trade_log=trade_log, selection_log=selection_log)
