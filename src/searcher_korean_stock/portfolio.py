from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd


@dataclass
class TradeRecord:
    date: pd.Timestamp
    ticker: str
    buy_price: float
    sell_price: float
    return_pct: float
    result: str


@dataclass
class Portfolio:
    initial_capital: float
    equity_curve: List[float] = field(default_factory=list)
    dates: List[pd.Timestamp] = field(default_factory=list)
    trades: List[TradeRecord] = field(default_factory=list)

    def __post_init__(self):
        self.cash = self.initial_capital
        self.equity_curve.append(self.cash)

    def allocate(self, n_positions: int) -> float:
        if n_positions == 0:
            return 0.0
        return self.cash / n_positions

    def update_equity(self, date: pd.Timestamp, pnl: float):
        self.cash += pnl
        self.dates.append(date)
        self.equity_curve.append(self.cash)

    def log_trade(self, record: TradeRecord):
        self.trades.append(record)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([t.__dict__ for t in self.trades])
