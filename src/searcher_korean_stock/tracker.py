"""
검색 결과 추적 모듈
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from dataclasses import dataclass, asdict

@dataclass
class TrackingResult:
    """추적 결과"""
    date: str
    ticker: str
    stock_name: str
    buy_price: float
    next_day_high: float
    next_day_close: float
    conditions_met: int
    score: float
    achieved: bool  # +1% 달성 여부
    actual_return: float  # 실제 수익률


class SearchTracker:
    """검색 결과 추적 관리자"""
    
    def __init__(self, data_dir: str = ".tracking"):
        """초기화"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db_file = os.path.join(data_dir, "tracking.json")
        self._load_db()
    
    def _load_db(self) -> None:
        """데이터베이스 로드"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
            except:
                self.db = {}
        else:
            self.db = {}
    
    def _save_db(self) -> None:
        """데이터베이스 저장"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
    
    def add_search_results(self, search_date: str, candidates: List[Any]) -> None:
        """
        검색 결과 저장
        
        Args:
            search_date: 검색 날짜 (YYYY-MM-DD)
            candidates: 검색된 종목 리스트 (SearchResult 객체)
        """
        if search_date not in self.db:
            self.db[search_date] = {
                "search_results": [],
                "tracking_results": [],
                "created_at": datetime.now().isoformat()
            }
        
        # 검색 결과 저장 (상위 5개)
        search_results = []
        for i, candidate in enumerate(candidates[:5]):
            search_results.append({
                "rank": i + 1,
                "ticker": candidate.ticker,
                "stock_name": candidate.stock_name,
                "buy_price": float(candidate.close),
                "conditions_met": candidate.conditions_met,
                "score": float(candidate.score),
                "conditions_detail": candidate.conditions_detail
            })
        
        self.db[search_date]["search_results"] = search_results
        self._save_db()
    
    def update_tracking_results(self, search_date: str, price_data: Dict[str, pd.DataFrame]) -> None:
        """
        다음날 실제 결과 업데이트
        
        Args:
            search_date: 검색 날짜 (YYYY-MM-DD)
            price_data: {ticker: DataFrame} 형태의 가격 데이터
        """
        if search_date not in self.db:
            return
        
        search_results = self.db[search_date].get("search_results", [])
        tracking_results = []
        
        for result in search_results:
            ticker = result["ticker"]
            
            if ticker not in price_data:
                continue
            
            df = price_data[ticker]
            if len(df) < 2:
                continue
            
            # 마지막 행 (검색 날짜)과 그 다음 행 (다음날)
            buy_price = result["buy_price"]
            
            # 다음날 데이터 찾기
            next_day_data = None
            for i in range(len(df) - 1):
                if df.iloc[i]['close'] == buy_price or abs(df.iloc[i]['close'] - buy_price) < 0.01:
                    if i + 1 < len(df):
                        next_day_data = df.iloc[i + 1]
                    break
            
            if next_day_data is None and len(df) >= 2:
                next_day_data = df.iloc[-1]
            
            if next_day_data is not None:
                next_day_high = float(next_day_data['high'])
                next_day_close = float(next_day_data['close'])
                
                # +1% 달성 여부
                actual_return = (next_day_high - buy_price) / buy_price
                achieved = actual_return >= 0.01
                
                tracking_results.append({
                    "ticker": ticker,
                    "stock_name": result["stock_name"],
                    "buy_price": buy_price,
                    "next_day_high": next_day_high,
                    "next_day_close": next_day_close,
                    "conditions_met": result["conditions_met"],
                    "score": result["score"],
                    "achieved": achieved,
                    "actual_return": float(actual_return)
                })
        
        self.db[search_date]["tracking_results"] = tracking_results
        self.db[search_date]["tracked_at"] = datetime.now().isoformat()
        self._save_db()
    
    def get_today_search_results(self) -> Dict[str, Any]:
        """오늘 검색 결과 가져오기"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.db.get(today, {})
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계 계산"""
        total_searches = 0
        total_candidates = 0
        total_achieved = 0
        accuracy_rate = 0.0
        
        all_results = []
        
        for date, data in self.db.items():
            search_results = data.get("search_results", [])
            tracking_results = data.get("tracking_results", [])
            
            if search_results:
                total_searches += 1
                total_candidates += len(search_results)
                all_results.extend(tracking_results)
                total_achieved += sum(1 for r in tracking_results if r.get("achieved", False))
        
        if total_candidates > 0:
            accuracy_rate = total_achieved / total_candidates
        
        # 점수 기반 분석
        avg_score = 0.0
        avg_conditions = 0
        if all_results:
            avg_score = sum(r.get("score", 0) for r in all_results) / len(all_results)
            avg_conditions = sum(r.get("conditions_met", 0) for r in all_results) / len(all_results)
        
        return {
            "total_searches": total_searches,
            "total_candidates": total_candidates,
            "total_achieved": total_achieved,
            "accuracy_rate": accuracy_rate,
            "avg_score": avg_score,
            "avg_conditions": avg_conditions,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_history_dataframe(self, limit: int = 50) -> pd.DataFrame:
        """히스토리를 DataFrame으로 반환"""
        records = []
        
        # 역순으로 정렬 (최신부터)
        for date in sorted(self.db.keys(), reverse=True)[:limit]:
            data = self.db[date]
            tracking_results = data.get("tracking_results", [])
            
            for result in tracking_results:
                records.append({
                    "검색날짜": date,
                    "종목명": result.get("stock_name", ""),
                    "종목코드": result.get("ticker", ""),
                    "매수가": result.get("buy_price", 0),
                    "다음고가": result.get("next_day_high", 0),
                    "수익률": result.get("actual_return", 0),
                    "조건충족": result.get("conditions_met", 0),
                    "점수": result.get("score", 0),
                    "달성": "✅" if result.get("achieved", False) else "❌"
                })
        
        if not records:
            return pd.DataFrame()
        
        return pd.DataFrame(records)
    
    def get_date_summary(self) -> pd.DataFrame:
        """날짜별 요약"""
        summaries = []
        
        for date in sorted(self.db.keys(), reverse=True):
            data = self.db[date]
            search_results = data.get("search_results", [])
            tracking_results = data.get("tracking_results", [])
            
            if search_results:
                achieved_count = sum(1 for r in tracking_results if r.get("achieved", False))
                accuracy = achieved_count / len(search_results) if search_results else 0
                
                summaries.append({
                    "날짜": date,
                    "검색종목": len(search_results),
                    "달성종목": achieved_count,
                    "정확도": f"{accuracy:.1%}",
                    "평균점수": f"{sum(r.get('score', 0) for r in search_results) / len(search_results):.1%}",
                    "평균조건": f"{sum(r.get('conditions_met', 0) for r in search_results) / len(search_results):.1f}/6"
                })
        
        if not summaries:
            return pd.DataFrame()
        
        return pd.DataFrame(summaries)


# 전역 인스턴스
tracker = SearchTracker()
