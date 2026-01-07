from __future__ import annotations

import base64
import io
from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string, request

from .data_loader import KoreanStockLoader
from .strategy import select_candidates
from .backtester import simulate
from .visualizer import equity_curve, performance_summary


TEMPLATE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>한국 주식 단타 스캐너</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      padding: 40px;
    }
    header {
      text-align: center;
      margin-bottom: 40px;
      border-bottom: 3px solid #667eea;
      padding-bottom: 20px;
    }
    h1 {
      font-size: 2.5em;
      color: #333;
      margin-bottom: 10px;
    }
    .subtitle {
      color: #666;
      font-size: 1.1em;
    }
    
    .search-box {
      background: #f8f9fa;
      border: 2px solid #e9ecef;
      border-radius: 12px;
      padding: 30px;
      margin-bottom: 40px;
    }
    .search-box h3 {
      color: #333;
      margin-bottom: 20px;
      font-size: 1.2em;
    }
    .search-form {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      align-items: end;
    }
    .form-group {
      display: flex;
      flex-direction: column;
    }
    .form-group label {
      font-size: 0.95em;
      font-weight: 600;
      color: #333;
      margin-bottom: 8px;
    }
    .form-group select,
    .form-group input {
      padding: 12px;
      border: 1px solid #ddd;
      border-radius: 8px;
      font-size: 1em;
      background: white;
      color: #333;
    }
    .form-group select:focus,
    .form-group input:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .btn-search {
      padding: 12px 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1em;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .btn-search:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .btn-search:active {
      transform: translateY(0);
    }
    .btn-search:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 25px;
      border-radius: 12px;
      text-align: center;
      box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .stat-label {
      font-size: 0.9em;
      opacity: 0.9;
      margin-bottom: 10px;
    }
    .stat-value {
      font-size: 2em;
      font-weight: bold;
    }
    .section {
      margin-bottom: 40px;
    }
    .section h2 {
      font-size: 1.8em;
      color: #333;
      margin-bottom: 20px;
      border-left: 4px solid #667eea;
      padding-left: 15px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    th {
      background: #667eea;
      color: white;
      padding: 15px;
      text-align: left;
      font-weight: 600;
    }
    td {
      padding: 12px 15px;
      border-bottom: 1px solid #eee;
    }
    tr:hover {
      background: #f8f9ff;
    }
    tr:last-child td {
      border-bottom: none;
    }
    .positive { color: #10b981; font-weight: 600; }
    .negative { color: #ef4444; font-weight: 600; }
    .chart-container {
      text-align: center;
      margin-top: 30px;
      background: #f8f9fa;
      padding: 20px;
      border-radius: 12px;
    }
    .chart-container img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
    .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #667eea;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 20px auto;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .error {
      background: #fee;
      color: #c33;
      padding: 20px;
      border-radius: 8px;
      margin: 20px 0;
      border-left: 4px solid #c33;
    }
    .placeholder {
      text-align: center;
      color: #999;
      padding: 40px;
      font-size: 1.1em;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>📈 한국 주식 단타 스캐너</h1>
      <p class="subtitle">실시간 데이터 기반 +2% 목표 종목 검색 및 백테스트</p>
    </header>

    <div class="search-box">
      <h3>🔍 검색 조건</h3>
      <form method="get" class="search-form" id="searchForm">
        <div class="form-group">
          <label for="days">조회 기간 (일)</label>
          <select id="days" name="days" required>
            <option value="30">30일</option>
            <option value="60" selected>60일</option>
            <option value="90">90일</option>
            <option value="180">180일</option>
            <option value="365">1년</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="num_stocks">검색 종목 수</label>
          <select id="num_stocks" name="num_stocks" required>
            <option value="5">5개</option>
            <option value="10" selected>10개</option>
            <option value="20">20개</option>
            <option value="50">50개</option>
          </select>
        </div>
        
        <div class="form-group">
          <button type="submit" class="btn-search" id="searchBtn">🔎 검색 시작</button>
        </div>
      </form>
    </div>

    {% if loading %}
    <div class="loading">
      <div class="spinner"></div>
      <p>데이터를 로드하는 중입니다. 잠시만 기다려주세요...</p>
    </div>
    {% elif error %}
    <div class="error">
      <strong>⚠️ 오류:</strong> {{ error }}
    </div>
    {% elif has_data %}

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">승률</div>
        <div class="stat-value">{{ '{:.1%}'.format(summary.win_rate) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">평균 수익률</div>
        <div class="stat-value {% if summary.avg_return >= 0 %}positive{% else %}negative{% endif %}">
          {{ '{:+.2%}'.format(summary.avg_return) }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">최대손실(MDD)</div>
        <div class="stat-value">{{ '{:.2%}'.format(summary.mdd) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">총 거래</div>
        <div class="stat-value">{{ num_trades }}</div>
      </div>
    </div>

    <div class="section">
      <h2>🎯 14:50 조건 충족 종목 (상위 4개)</h2>
      {% if candidates %}
      <table>
        <thead>
          <tr>
            <th style="width: 15%;">날짜</th>
            <th style="width: 15%;">티커</th>
            <th style="width: 30%; text-align: right;">종가</th>
            <th style="width: 40%; text-align: right;">점수</th>
          </tr>
        </thead>
        <tbody>
        {% for row in candidates %}
          <tr>
            <td>{{ row.date }}</td>
            <td><strong>{{ row.ticker }}</strong></td>
            <td style="text-align: right;">{{ '{:,.0f}'.format(row.close) }}</td>
            <td style="text-align: right;">{{ '{:.3f}'.format(row.total_score) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
        <p style="padding: 20px; color: #666;">조건을 만족하는 종목이 없습니다.</p>
      {% endif %}
    </div>

    <div class="section">
      <h2>📊 최근 거래 로그 (상위 10건)</h2>
      {% if trades %}
      <table>
        <thead>
          <tr>
            <th style="width: 12%;">날짜</th>
            <th style="width: 10%;">티커</th>
            <th style="width: 15%; text-align: right;">매수가</th>
            <th style="width: 15%; text-align: right;">매도가</th>
            <th style="width: 18%; text-align: right;">수익률</th>
            <th style="width: 15%; text-align: center;">결과</th>
          </tr>
        </thead>
        <tbody>
        {% for row in trades %}
          <tr>
            <td>{{ row.date }}</td>
            <td><strong>{{ row.ticker }}</strong></td>
            <td style="text-align: right;">{{ '{:,.0f}'.format(row.buy_price) }}</td>
            <td style="text-align: right;">{{ '{:,.0f}'.format(row.sell_price) }}</td>
            <td style="text-align: right;" class="{% if row.return_pct > 0 %}positive{% else %}negative{% endif %}">
              {{ '{:+.2%}'.format(row.return_pct) }}
            </td>
            <td style="text-align: center;">
              <span style="{% if row.result == 'win' %}color: #10b981; font-weight: bold;{% else %}color: #ef4444; font-weight: bold;{% endif %}">
                {% if row.result == 'win' %}✓ 승{% elif row.result == 'loss' %}✗ 패{% else %}- 보유{% endif %}
              </span>
            </td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
        <p style="padding: 20px; color: #666;">거래 로그가 없습니다.</p>
      {% endif %}
    </div>

    <div class="section chart-container">
      <h2>📈 누적 자산 곡선</h2>
      {% if equity_image %}
        <img src="data:image/png;base64,{{ equity_image }}" alt="누적 자산 곡선" />
      {% else %}
        <p style="color: #666;">그래프를 표시할 수 없습니다.</p>
      {% endif %}
    </div>

    <div class="section">
      <h2>💹 오늘 거래량 TOP 10</h2>
      {% if top_volume_stocks %}
      <table>
        <thead>
          <tr>
            <th style="width: 8%; text-align: center;">순위</th>
            <th style="width: 30%;">종목명</th>
            <th style="width: 12%; text-align: center;">종목코드</th>
            <th style="width: 15%; text-align: right;">현재가</th>
            <th style="width: 17%; text-align: right;">거래량</th>
            <th style="width: 18%; text-align: right;">거래대금</th>
          </tr>
        </thead>
        <tbody>
        {% for row in top_volume_stocks %}
          <tr>
            <td style="text-align: center; font-weight: bold; color: #667eea;">{{ loop.index }}</td>
            <td><strong>{{ row.stock_name }}</strong></td>
            <td style="text-align: center; font-family: monospace; font-weight: bold;">{{ row.ticker }}</td>
            <td style="text-align: right;">{{ '{:,.0f}'.format(row.close) }}</td>
            <td style="text-align: right;">{{ '{:,.0f}'.format(row.volume) }}</td>
            <td style="text-align: right; color: #667eea; font-weight: bold;">{{ '{:,.0f}'.format(row.amount) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
        <p style="padding: 20px; color: #666;">데이터를 불러올 수 없습니다.</p>
      {% endif %}
    </div>

    {% else %}
    <div class="placeholder">
      🔍 검색 조건을 선택하고 "검색 시작" 버튼을 클릭해주세요.
    </div>
    {% endif %}
  </div>
  
  <script>
    document.getElementById('searchForm').addEventListener('submit', function(e) {
      const btn = document.getElementById('searchBtn');
      btn.disabled = true;
      btn.textContent = '⏳ 검색 중...';
    });
  </script>
</body>
</html>
"""


def _load_data(days: int = 60) -> pd.DataFrame:
    """실시간 한국 주식 데이터 로드."""
    loader = KoreanStockLoader(days=days)
    return loader.load()


# 종목 이름 매핑
STOCK_NAMES = {
    '005930': 'Samsung Electronics',
    '000660': 'SK Hynix',
    '051910': 'LG Chem',
    '207940': 'Samsung SDI',
    '006400': 'Samsung SDI',
    '035720': 'Kakao',
    '012330': 'Hyundai Motor',
    '005380': 'Hyundai Motor',
    '055550': 'Shinhan Finance',
    '032830': 'Samsung Life',
}


def _add_stock_names(df: pd.DataFrame) -> pd.DataFrame:
    """데이터프레임에 종목 이름 추가"""
    df = df.copy()
    df['stock_name'] = df['ticker'].map(STOCK_NAMES).fillna(df['ticker'])
    return df


def _plot_equity(portfolio) -> str:
    """자산 곡선을 이미지로 변환."""
    fig = equity_curve(portfolio)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return encoded


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        # GET 파라미터에서 days와 num_stocks 받기
        days = request.args.get("days", type=int)
        num_stocks = request.args.get("num_stocks", type=int)
        
        # 항상 거래량 TOP 10을 표시하기 위해 기본 데이터 로드
        try:
            df_for_volume = _load_data(days=60)
            latest_date = df_for_volume['date'].max()
            latest_df = df_for_volume[df_for_volume['date'] == latest_date].copy()
            top_volume = latest_df.nlargest(10, 'volume')[['ticker', 'close', 'volume', 'amount']]
            top_volume = _add_stock_names(top_volume)
            top_volume_records = top_volume[['stock_name', 'ticker', 'close', 'volume', 'amount']].to_dict('records')
        except:
            top_volume_records = []
        
        # 검색 버튼이 클릭되지 않았으면 초기 페이지만 렌더링
        if days is None or num_stocks is None:
            return render_template_string(
                TEMPLATE,
                candidates=[],
                trades=[],
                summary={'win_rate': 0, 'avg_return': 0, 'mdd': 0},
                num_trades=0,
                equity_image=None,
                top_volume_stocks=top_volume_records,
                error=None,
                loading=False,
                has_data=False,
            )
        
        try:
            df = _load_data(days=days)

            candidates_df = select_candidates(df)
            candidates = candidates_df[['date', 'ticker', 'close', 'total_score']].tail(4)
            candidates_records = candidates.assign(date=candidates['date'].dt.strftime('%Y-%m-%d')).to_dict('records')

            backtest_result = simulate(df)
            trade_log = backtest_result.trade_log.tail(10).copy()
            if not trade_log.empty and 'date' in trade_log.columns:
                trade_log['date'] = pd.to_datetime(trade_log['date']).dt.strftime('%Y-%m-%d')
            trades = trade_log.to_dict('records')

            summary = performance_summary(trade_log)
            equity_image = _plot_equity(backtest_result.portfolio)
            
            # 오늘 거래량 상위 10개 종목
            latest_date = df['date'].max()
            latest_df = df[df['date'] == latest_date].copy()
            top_volume = latest_df.nlargest(10, 'volume')[['ticker', 'close', 'volume', 'amount']]
            top_volume = _add_stock_names(top_volume)
            top_volume_records = top_volume[['stock_name', 'ticker', 'close', 'volume', 'amount']].to_dict('records')

            return render_template_string(
                TEMPLATE,
                candidates=candidates_records,
                trades=trades,
                summary=summary,
                num_trades=len(backtest_result.trade_log),
                equity_image=equity_image,
                top_volume_stocks=top_volume_records,
                error=None,
                loading=False,
                has_data=True,
            )
        except Exception as e:
            return render_template_string(
                TEMPLATE,
                candidates=[],
                trades=[],
                summary={'win_rate': 0, 'avg_return': 0, 'mdd': 0},
                num_trades=0,
                equity_image=None,
                top_volume_stocks=top_volume_records,
                error=str(e),
                loading=False,
                has_data=False,
            ), 500

    return app


def run():
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)


if __name__ == "__main__":
    run()
