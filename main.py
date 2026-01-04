"""다음날 +2% 목표 단타 종목 검색기 & 백테스터 예제 실행."""

from pathlib import Path

import pandas as pd

from src.searcher_korean_stock.data_loader import CSVLoader
from src.searcher_korean_stock.backtester import simulate
from src.searcher_korean_stock.strategy import select_candidates
from src.searcher_korean_stock.visualizer import equity_curve, performance_summary


def run(data_path: str = 'data/sample_prices.csv'):
    loader = CSVLoader(data_path)
    df = loader.load()

    # 종목 검색
    candidates = select_candidates(df)
    print('### 14:50 조건 충족 종목 (상위 4개)')
    print(candidates[['date', 'ticker', 'close', 'total_score']].tail())

    # 백테스트
    result = simulate(df)
    trade_log = result.trade_log
    print('\n### 거래 로그 (최근 5건)')
    print(trade_log.tail())

    summary = performance_summary(trade_log)
    print('\n승률: {:.2%}, 평균 수익률: {:.2%}, MDD: {:.2%}'.format(summary['win_rate'], summary['avg_return'], summary['mdd']))
    print('\n월별 수익률')
    print(summary['monthly_returns'])
    print('\n주별 수익률')
    print(summary['weekly_returns'])

    # 자산 곡선 시각화 파일 저장
    fig = equity_curve(result.portfolio)
    output_path = Path('equity_curve.png')
    fig.savefig(output_path)
    print(f'누적 자산 그래프 저장: {output_path.resolve()}')


if __name__ == '__main__':
    run()
