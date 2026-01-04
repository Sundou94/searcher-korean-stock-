from __future__ import annotations

import base64
import io
from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string, request

from .data_loader import CSVLoader
from .strategy import select_candidates
from .backtester import simulate
from .visualizer import equity_curve, performance_summary


TEMPLATE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>다음날 +2% 스캐너</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
    th { background: #f5f5f5; }
    h2 { margin-top: 24px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .equity { text-align: center; }
    form { margin-bottom: 16px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>다음날 +2% 목표 단타 스캐너 & 백테스터</h1>
    <form method="get">
      <label>CSV 경로: <input type="text" name="data_path" size="40" value="{{ data_path }}" /></label>
      <button type="submit">불러오기</button>
    </form>

    <h2>14:50 조건 충족 종목 (상위 4개)</h2>
    {% if candidates %}
    <table>
      <thead><tr><th>날짜</th><th>티커</th><th>종가</th><th>점수</th></tr></thead>
      <tbody>
      {% for row in candidates %}
        <tr><td>{{ row.date }}</td><td style="text-align:left">{{ row.ticker }}</td><td>{{ '{:,.0f}'.format(row.close) }}</td><td>{{ '{:.3f}'.format(row.total_score) }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
      <p>조건을 만족하는 종목이 없습니다.</p>
    {% endif %}

    <h2>성과 요약</h2>
    <ul>
      <li>승률: {{ '{:.2%}'.format(summary.win_rate) }}</li>
      <li>평균 수익률: {{ '{:.2%}'.format(summary.avg_return) }}</li>
      <li>MDD: {{ '{:.2%}'.format(summary.mdd) }}</li>
    </ul>

    <h3>월별 수익률</h3>
    <table>
      <thead><tr><th>월</th><th>수익률</th></tr></thead>
      <tbody>
        {% for period, value in summary.monthly_returns.items() %}
          <tr><td style="text-align:left">{{ period }}</td><td>{{ '{:.2%}'.format(value) }}</td></tr>
        {% endfor %}
      </tbody>
    </table>

    <h3>주별 수익률</h3>
    <table>
      <thead><tr><th>주</th><th>수익률</th></tr></thead>
      <tbody>
        {% for period, value in summary.weekly_returns.items() %}
          <tr><td style="text-align:left">{{ period }}</td><td>{{ '{:.2%}'.format(value) }}</td></tr>
        {% endfor %}
      </tbody>
    </table>

    <h2>최근 거래 로그 (상위 10건)</h2>
    <table>
      <thead><tr><th>날짜</th><th>티커</th><th>매수가</th><th>매도가</th><th>수익률</th><th>승패</th></tr></thead>
      <tbody>
        {% for row in trades %}
          <tr>
            <td>{{ row.date }}</td>
            <td style="text-align:left">{{ row.ticker }}</td>
            <td>{{ '{:,.0f}'.format(row.entry_price) }}</td>
            <td>{{ '{:,.0f}'.format(row.exit_price) }}</td>
            <td>{{ '{:.2%}'.format(row.return_rate) }}</td>
            <td>{{ '승' if row.win else '패' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    <div class="equity">
      <h2>누적 자산 곡선</h2>
      {% if equity_image %}
        <img src="data:image/png;base64,{{ equity_image }}" alt="Equity Curve" />
      {% else %}
        <p>그래프를 표시할 수 없습니다.</p>
      {% endif %}
    </div>
  </div>
</body>
</html>
"""


def _load_data(data_path: str | Path) -> pd.DataFrame:
    loader = CSVLoader(data_path)
    return loader.load()


def _plot_equity(portfolio) -> str:
    fig = equity_curve(portfolio)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return encoded


def create_app(default_path: str | Path = "data/sample_prices.csv") -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        data_path = request.args.get("data_path", str(default_path))
        df = _load_data(data_path)

        candidates_df = select_candidates(df)
        candidates = candidates_df[['date', 'ticker', 'close', 'total_score']].tail(4)
        candidates_records = candidates.assign(date=candidates['date'].dt.strftime('%Y-%m-%d')).to_dict('records')

        backtest_result = simulate(df)
        trade_log = backtest_result.trade_log.tail(10).copy()
        trade_log['date'] = pd.to_datetime(trade_log['date']).dt.strftime('%Y-%m-%d')
        trades = trade_log.to_dict('records')

        summary = performance_summary(trade_log)
        equity_image = _plot_equity(backtest_result.portfolio)

        return render_template_string(
            TEMPLATE,
            data_path=data_path,
            candidates=candidates_records,
            trades=trades,
            summary=summary,
            equity_image=equity_image,
        )

    return app


def run():
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == "__main__":
    run()
