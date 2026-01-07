"""
다음날 +1% 상승 검색기 - 데모 및 테스트 스크립트
"""
import sys
import os
import io

# UTF-8 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from searcher_korean_stock.config import SearchConfig
from searcher_korean_stock.data_loader import loader
from searcher_korean_stock.engine import DayTradeSearchEngine, BacktestEngine


def main():
    print("=" * 80)
    print("📈 다음날 +1% 상승 가능성 검색기")
    print("=" * 80)
    
    # 1. 데이터 로드
    print("\n📥 1단계: 데이터 로드 중...")
    try:
        data = loader.prepare_data(days=60)
        candidates_df = loader.get_today_candidates()
        print(f"✅ {len(candidates_df)} 개 종목 로드 완료")
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return
    
    # 2. 검색 실행
    print("\n🔍 2단계: 조건 기반 검색 중...")
    
    # 기본 설정 사용
    config = SearchConfig()
    engine = DayTradeSearchEngine(config)
    
    # 모든 조건을 평가
    all_results = engine.search(candidates_df, config)
    
    # 3개 이상 조건 충족하는 종목만 표시
    filtered_results = [r for r in all_results if r.conditions_met >= 3]
    
    print(f"✅ 검색 완료")
    print(f"   - 전체 평가 종목: {len(all_results)}")
    print(f"   - 3개 이상 조건 충족: {len(filtered_results)}")
    
    # 3. 검색 결과 표시
    print("\n📊 3단계: 검색 결과 (상위 10개)")
    print("-" * 80)
    print(f"{'순위':<4} {'종목명':<20} {'종목코드':<12} {'현재가':<12} {'조건충족':<8} {'점수':<8}")
    print("-" * 80)
    
    for i, result in enumerate(filtered_results[:10], 1):
        print(f"{i:<4} {result.stock_name:<20} {result.ticker:<12} "
              f"{result.close:>11,.0f} {result.conditions_met:>7}/6 {result.score:>7.1%}")
    
    # 4. 상위 종목 상세 분석
    if filtered_results:
        print("\n🔎 상위 종목 상세 분석")
        print("-" * 80)
        top_result = filtered_results[0]
        print(f"\n📌 {top_result.stock_name} ({top_result.ticker})")
        print(f"   현재가: {top_result.close:,.0f}원")
        print(f"   다음날 고가(예상): {top_result.next_high:,.0f}원")
        print(f"\n   조건 충족 현황:")
        
        condition_names = {
            'volume': '거래대금 증가',
            'candle': '양봉 조건',
            'close': '종가 위치',
            'trend': '단기 추세',
            'volatility': '변동성 필터',
            'size': '종목 규모'
        }
        
        for key, name in condition_names.items():
            result = top_result.conditions_detail.get(key, False)
            status = "✅ 충족" if result else "❌ 불충족"
            print(f"   · {name:<15} {status}")
    
    # 5. 백테스트
    print("\n" + "=" * 80)
    print("📈 백테스트 시뮬레이션")
    print("=" * 80)
    
    backtest_engine = BacktestEngine(config)
    backtest_results = backtest_engine.simulate_trade(filtered_results, data)
    
    print(f"\n성과 지표:")
    print(f"  거래 횟수: {backtest_results['total_trades']}")
    print(f"  승 / 패: {backtest_results['win_count']} / {backtest_results['total_trades'] - backtest_results['win_count']}")
    print(f"  승률: {backtest_results['win_rate']:.1%}")
    print(f"  평균 수익률: {backtest_results['avg_return']:.2%}")
    print(f"  총 수익률: {backtest_results['total_return']:.2%}")
    print(f"  최대 낙폭(MDD): {backtest_results['mdd']:.2%}")
    print(f"  초기 자산: {config.backtest.initial_capital:,}원")
    print(f"  최종 자산: {backtest_results['final_capital']:,.0f}원")
    
    # 거래 내역
    if backtest_results['trades']:
        print(f"\n상위 거래 (최신 5건):")
        print("-" * 80)
        print(f"{'종목코드':<12} {'매수가':<12} {'매도가':<12} {'수익률':<12} {'손익':<15}")
        print("-" * 80)
        
        for trade in backtest_results['trades'][-5:]:
            print(f"{trade['ticker']:<12} {trade['buy_price']:>11,.0f} {trade['sell_price']:>11,.0f} "
                  f"{trade['pnl_pct']:>11.2%} {trade['pnl_amount']:>14,.0f}원")
    
    print("\n" + "=" * 80)
    print("✅ 데모 완료")
    print("=" * 80)
    print("\n💡 팁: Streamlit UI를 사용하려면 다음을 실행하세요:")
    print("   python run_streamlit.py")
    print("   또는")
    print("   streamlit run app.py")


if __name__ == "__main__":
    main()
