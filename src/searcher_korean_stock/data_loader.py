"""
한국 주식 데이터 로더 - yfinance 기반
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pickle
import os


class KoreanStockDataLoader:
    """한국 주식 데이터를 yfinance에서 로드하는 클래스"""
    
    # 대표 KOSPI 종목들 (시가총액 순)
    SAMPLE_TICKERS = [
        '005930.KS',  # Samsung Electronics
        '000660.KS',  # SK Hynix
        '051910.KS',  # LG Chem
        '207940.KS',  # SM C&C
        '006400.KS',  # Samsung SDI
        '035720.KS',  # Kakao
        '012330.KS',  # Hyundai Motor
        '005380.KS',  # Hyundai Motor Finance
        '055550.KS',  # Shinhan Financial
        '032830.KS',  # Samsung Life Insurance
    ]
    
    # 종목명 매핑
    STOCK_NAMES = {
        '005930.KS': 'Samsung Electronics',
        '000660.KS': 'SK Hynix',
        '051910.KS': 'LG Chem',
        '207940.KS': 'SM C&C',
        '006400.KS': 'Samsung SDI',
        '035720.KS': 'Kakao',
        '012330.KS': 'Hyundai Motor',
        '005380.KS': 'Hyundai Motor Finance',
        '055550.KS': 'Shinhan Financial',
        '032830.KS': 'Samsung Life Insurance',
    }
    
    def __init__(self, cache_dir: str = ".cache"):
        """초기화"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, ticker: str, days: int) -> str:
        """캐시 파일 경로 생성"""
        filename = f"{ticker.replace('.', '_')}_{days}d.pkl"
        return os.path.join(self.cache_dir, filename)
    
    def load_stock_data(self, ticker: str, days: int = 60, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        단일 종목 데이터 로드
        
        Args:
            ticker: 종목 코드 (예: '005930.KS')
            days: 로드할 데이터 기간 (일)
            use_cache: 캐시 사용 여부
        
        Returns:
            OHLCV 데이터프레임 또는 None
        """
        cache_path = self.get_cache_path(ticker, days)
        
        # 캐시 확인
        if use_cache and os.path.exists(cache_path):
            try:
                df = pd.read_pickle(cache_path)
                # 캐시가 오늘 생성된 경우만 사용
                if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))).days == 0:
                    return df
            except Exception as e:
                print(f"캐시 로드 실패 {ticker}: {e}")
        
        try:
            # yfinance에서 데이터 로드
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                return None
            
            # 컬럼명 정규화
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df.columns = df.columns.str.lower()
            
            # 필요한 컬럼만 선택
            required_cols = ['open', 'high', 'low', 'close', 'volume', 'adj close']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols]
            
            # Close 사용
            if 'adj close' in df.columns and 'close' in df.columns:
                df = df.drop(columns=['adj close'])
            
            df = df.dropna()
            
            if df.empty:
                return None
            
            # 캐시 저장
            try:
                df.to_pickle(cache_path)
            except:
                pass
            
            return df
            
        except Exception as e:
            print(f"데이터 로드 실패 {ticker}: {e}")
            return None
    
    def load_multiple_stocks(self, tickers: List[str] = None, days: int = 60) -> Dict[str, pd.DataFrame]:
        """
        여러 종목 데이터 로드
        
        Args:
            tickers: 종목 코드 리스트 (None이면 기본 종목 사용)
            days: 로드할 데이터 기간
        
        Returns:
            {ticker: DataFrame} 딕셔너리
        """
        if tickers is None:
            tickers = self.SAMPLE_TICKERS
        
        data = {}
        for ticker in tickers:
            df = self.load_stock_data(ticker, days)
            if df is not None:
                data[ticker] = df
        
        return data
    
    def add_technical_indicators(self, df: pd.DataFrame, ticker: str = None) -> pd.DataFrame:
        """
        기술적 지표 추가
        
        Args:
            df: OHLCV 데이터프레임
            ticker: 종목 코드 (표시용)
        
        Returns:
            기술적 지표가 추가된 데이프레임
        """
        df = df.copy()
        
        # 거래량 비율 (당일 / 20일 평균)
        df['volume_avg_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg_20']
        df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
        
        # 거래대금
        df['amount'] = df['close'] * df['volume']
        df['amount_avg_20'] = df['amount'].rolling(window=20).mean()
        
        # 이동평균선
        for period in [5, 10, 20, 50]:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean()
        
        # 고점 롤링 (20일)
        df['high_max_20'] = df['high'].rolling(window=20).max()
        df['high_max_10'] = df['high'].rolling(window=10).max()
        
        # 저점 롤링 (20일)
        df['low_min_20'] = df['low'].rolling(window=20).min()
        df['low_min_10'] = df['low'].rolling(window=10).min()
        
        # 일변동률
        df['daily_change'] = (df['high'] - df['low']) / df['close']
        
        # 평균 일변동률 (10일)
        df['volatility'] = df['daily_change'].rolling(window=10).mean()
        df['volatility'] = df['volatility'].fillna(0)
        
        # 다음날 고가 (백테스트용)
        df['next_high'] = df['high'].shift(-1)
        
        # 시가총액 추정 (실제는 외부 데이터가 필요하지만 근사값 사용)
        df['market_cap'] = 1_000_000_000_000  # 기본값 1조 (실제는 API에서 조회 필요)
        
        return df
    
    def prepare_data(self, days: int = 60, tickers: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        검색기용 데이터 준비
        
        Args:
            days: 조회 기간
            tickers: 종목 코드 리스트
        
        Returns:
            {ticker: prepared_dataframe} 딕셔너리
        """
        # 데이터 로드
        data = self.load_multiple_stocks(tickers, days)
        
        # 기술적 지표 추가
        prepared_data = {}
        for ticker, df in data.items():
            prepared_df = self.add_technical_indicators(df, ticker)
            prepared_data[ticker] = prepared_df
        
        return prepared_data
    
    def get_today_candidates(self, tickers: List[str] = None) -> pd.DataFrame:
        """
        오늘 데이터 기반 전체 종목 반환 (검색용)
        
        Args:
            tickers: 종목 코드 리스트
        
        Returns:
            모든 종목의 최신 데이터를 행으로 하는 DataFrame
        """
        data = self.prepare_data(days=60, tickers=tickers)
        
        records = []
        for ticker, df in data.items():
            if len(df) > 0:
                latest = df.iloc[-1].to_dict()
                latest['ticker'] = ticker
                latest['stock_name'] = self.STOCK_NAMES.get(ticker, ticker)
                records.append(latest)
        
        if not records:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(records)
        return result_df


# 전역 인스턴스
loader = KoreanStockDataLoader()
