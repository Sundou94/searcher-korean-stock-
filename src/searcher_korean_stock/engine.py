"""
다음날 +1% 상승 검색 엔진
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

from .config import SearchConfig, VolumeCondition, CandleCondition, ClosePositionCondition, \
    TrendCondition, VolatilityCondition, SizeCondition


@dataclass
class SearchResult:
    """검색 결과"""
    ticker: str
    stock_name: str
    close: float
    next_high: float
    conditions_met: int  # 충족한 조건 개수
    conditions_detail: Dict[str, bool]  # 각 조건별 충족 여부
    score: float = 0.0  # 가중 점수


class DayTradeSearchEngine:
    """다음날 +1% 상승 가능성 검색 엔진"""
    
    def __init__(self, config: SearchConfig = None):
        """초기화"""
        self.config = config or SearchConfig()
    
    def evaluate_single_row(self, row: Dict[str, Any], config: SearchConfig) -> Tuple[int, Dict[str, bool], float]:
        """
        단일 행(주식 데이터)에 대해 모든 조건 평가
        
        Args:
            row: 주식 데이터 (딕셔너리)
            config: 검색 설정
        
        Returns:
            (충족 조건 개수, 조건별 결과 딕셔너리, 점수)
        """
        conditions_detail = {}
        scores = {}
        
        # 1. 거래대금 증가
        vol_result = VolumeCondition.validate(row, config.volume)
        conditions_detail['volume'] = vol_result
        scores['volume'] = 1.0 if vol_result else 0.0
        
        # 2. 양봉 조건
        candle_result = CandleCondition.validate(row, config.candle)
        conditions_detail['candle'] = candle_result
        scores['candle'] = 1.0 if candle_result else 0.0
        
        # 3. 종가 위치
        close_result = ClosePositionCondition.validate(row, config.close)
        conditions_detail['close'] = close_result
        scores['close'] = 1.0 if close_result else 0.0
        
        # 4. 단기 추세
        trend_result = TrendCondition.validate(row, config.trend)
        conditions_detail['trend'] = trend_result
        scores['trend'] = 1.0 if trend_result else 0.0
        
        # 5. 변동성
        volatility_result = VolatilityCondition.validate(row, config.volatility)
        conditions_detail['volatility'] = volatility_result
        scores['volatility'] = 1.0 if volatility_result else 0.0
        
        # 6. 종목 규모
        size_result = SizeCondition.validate(row, config.size)
        conditions_detail['size'] = size_result
        scores['size'] = 1.0 if size_result else 0.0
        
        # 충족 조건 개수
        conditions_met = sum(1 for v in conditions_detail.values() if v)
        
        # 점수 계산
        if config.scoring_enabled:
            score = sum(scores.get(k, 0) * config.weights.get(k, 0) 
                       for k in config.weights.keys())
        else:
            score = conditions_met / len(conditions_detail)
        
        return conditions_met, conditions_detail, score
    
    def search(self, df: pd.DataFrame, config: SearchConfig = None) -> List[SearchResult]:
        """
        종목 리스트에서 조건을 만족하는 종목 검색
        
        Args:
            df: 종목 데이터 (열: ticker, stock_name, close, next_high, 기술적 지표 등)
            config: 검색 설정 (None이면 self.config 사용)
        
        Returns:
            SearchResult 리스트 (점수 순 정렬)
        """
        config = config or self.config
        results = []
        
        for _, row in df.iterrows():
            conditions_met, conditions_detail, score = self.evaluate_single_row(row.to_dict(), config)
            
            result = SearchResult(
                ticker=row.get('ticker', ''),
                stock_name=row.get('stock_name', ''),
                close=row.get('close', 0),
                next_high=row.get('next_high', 0),
                conditions_met=conditions_met,
                conditions_detail=conditions_detail,
                score=score
            )
            results.append(result)
        
        # 점수 순 정렬
        results.sort(key=lambda x: (-x.score, -x.conditions_met))
        
        return results
    
    def search_by_min_conditions(self, df: pd.DataFrame, min_conditions: int = 4, 
                                 config: SearchConfig = None) -> List[SearchResult]:
        """
        최소 조건 개수 이상을 만족하는 종목만 필터링
        
        Args:
            df: 종목 데이터
            min_conditions: 최소 충족 조건 개수
            config: 검색 설정
        
        Returns:
            필터링된 SearchResult 리스트
        """
        all_results = self.search(df, config)
        return [r for r in all_results if r.conditions_met >= min_conditions]


class BacktestEngine:
    """백테스트 엔진"""
    
    def __init__(self, config: SearchConfig = None):
        """초기화"""
        self.config = config or SearchConfig()
    
    def simulate_trade(self, candidates: List[SearchResult], 
                      price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        후보 종목들에 대해 백테스트 실행
        
        Args:
            candidates: 검색된 후보 종목 리스트
            price_data: {ticker: DataFrame} 형태의 가격 데이터
        
        Returns:
            {
                'trades': 거래 리스트,
                'daily_returns': 일별 수익률,
                'cumulative_return': 누적 수익률,
                'win_rate': 승률,
                'avg_return': 평균 수익률,
                'mdd': 최대 낙폭,
                'final_capital': 최종 자산
            }
        """
        capital = self.config.backtest.initial_capital
        trades = []
        daily_equity = [capital]
        
        for candidate in candidates:
            ticker = candidate.ticker
            
            if ticker not in price_data:
                continue
            
            df = price_data[ticker]
            if len(df) < 2:
                continue
            
            # 당일 종가로 매수
            buy_price = candidate.close
            position_size = capital / len(candidates) if self.config.backtest.equal_weight else capital
            shares = int(position_size / buy_price)
            
            if shares == 0:
                continue
            
            # 다음날 고가로 매도 (또는 손절)
            next_high = candidate.next_high
            
            if pd.isna(next_high) or next_high == 0:
                continue
            
            # 손익 계산
            sell_price = next_high
            pnl_pct = (sell_price - buy_price) / buy_price
            
            # 익절/손절 적용
            if pnl_pct >= self.config.backtest.take_profit:
                sell_price = buy_price * (1 + self.config.backtest.take_profit)
                pnl_pct = self.config.backtest.take_profit
            elif pnl_pct <= self.config.backtest.stop_loss:
                sell_price = buy_price * (1 + self.config.backtest.stop_loss)
                pnl_pct = self.config.backtest.stop_loss
            
            pnl_amount = shares * (sell_price - buy_price)
            capital += pnl_amount
            
            trades.append({
                'ticker': ticker,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'shares': shares,
                'pnl_amount': pnl_amount,
                'pnl_pct': pnl_pct,
                'win': pnl_pct > 0
            })
            
            daily_equity.append(capital)
        
        # 성과 지표 계산
        if len(trades) == 0:
            return {
                'trades': [],
                'daily_equity': daily_equity,
                'total_trades': 0,
                'win_count': 0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'total_return': 0.0,
                'mdd': 0.0,
                'final_capital': capital
            }
        
        # 승률
        win_count = sum(1 for t in trades if t['win'])
        win_rate = win_count / len(trades) if len(trades) > 0 else 0
        
        # 평균 수익률
        avg_return = np.mean([t['pnl_pct'] for t in trades])
        
        # 총 수익률
        total_return = (capital - self.config.backtest.initial_capital) / self.config.backtest.initial_capital
        
        # 최대 낙폭 (MDD)
        cummax = np.maximum.accumulate(daily_equity)
        mdd = np.min((np.array(daily_equity) - cummax) / cummax) if len(daily_equity) > 0 else 0
        
        return {
            'trades': trades,
            'daily_equity': daily_equity,
            'total_trades': len(trades),
            'win_count': win_count,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_return': total_return,
            'mdd': mdd,
            'final_capital': capital
        }
