from __future__ import annotations

import abc
from pathlib import Path
from typing import Protocol

import pandas as pd


class DataLoader(Protocol):
    def load(self) -> pd.DataFrame:
        """Return dataframe with at least columns: date, ticker, open, high, low, close, volume, amount, after_13_amount, after_13_low, after_13_high, market_cap."""


class CSVLoader:
    """Simple CSV-based loader.

    The loader expects a CSV with columns:
    date, ticker, open, high, low, close, volume, amount, after_13_amount, after_13_low, after_13_high, market_cap
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(['ticker', 'date'], inplace=True)
        return df


class APILoader(abc.ABC):
    """Abstract API loader for live data ingestion."""

    @abc.abstractmethod
    def fetch(self) -> pd.DataFrame:
        raise NotImplementedError

    def load(self) -> pd.DataFrame:
        df = self.fetch()
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(['ticker', 'date'], inplace=True)
        return df
