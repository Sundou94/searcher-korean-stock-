from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt


def equity_curve(portfolio) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(portfolio.dates, portfolio.equity_curve[1:], label='Equity')
    ax.set_title('누적 자산 곡선')
    ax.set_xlabel('Date')
    ax.set_ylabel('KRW')
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    return fig


def performance_summary(trade_log: pd.DataFrame) -> dict:
    if trade_log.empty:
        return {'win_rate': 0.0, 'avg_return': 0.0, 'mdd': 0.0}

    win_rate = (trade_log['return_pct'] > 0).mean()
    avg_return = trade_log['return_pct'].mean()

    equity = trade_log['return_pct'].cumsum()
    rolling_max = equity.cummax()
    drawdown = equity - rolling_max
    mdd = drawdown.min()

    trade_log['date'] = pd.to_datetime(trade_log['date'])
    monthly = trade_log.groupby(trade_log['date'].dt.to_period('M'))['return_pct'].sum()
    weekly = trade_log.groupby(trade_log['date'].dt.to_period('W'))['return_pct'].sum()

    return {
        'win_rate': win_rate,
        'avg_return': avg_return,
        'mdd': mdd,
        'monthly_returns': monthly,
        'weekly_returns': weekly,
    }
