"""
다음날 +1% 상승 검색기 - 조건 정의 및 설정
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from enum import Enum


class ConditionType(Enum):
    """조건 타입"""
    VOLUME = "volume"           # 거래대금 증가
    CANDLE = "candle"           # 양봉 조건
    CLOSE_POSITION = "close"    # 종가 위치
    TREND = "trend"             # 단기 추세
    VOLATILITY = "volatility"   # 변동성
    SIZE = "size"               # 종목 규모


@dataclass
class VolumeCondition:
    """거래대금 증가 조건"""
    name: str = "거래대금 증가"
    enabled: bool = True
    multiplier: float = 2.0  # 최근 평균의 배수
    period: int = 20          # 평균 계산 기간
    description: str = "시장 참여 증가 여부 판단 (당일 거래대금 ≥ 최근 평균의 배수)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'VolumeCondition') -> bool:
        """거래대금 조건 검증"""
        if not config.enabled:
            return True
        return row.get('volume_ratio', 1.0) >= config.multiplier


@dataclass
class CandleCondition:
    """양봉 조건"""
    name: str = "양봉 조건"
    enabled: bool = True
    body_ratio_min: float = 0.3  # 몸통 비율 최소값
    description: str = "장 마감 기준 매수 우위 여부 (종가 > 시가, 몸통 비율 조절 가능)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'CandleCondition') -> bool:
        """양봉 조건 검증"""
        if not config.enabled:
            return True
        
        close = row.get('close', 0)
        open_price = row.get('open', 0)
        high = row.get('high', 0)
        
        if close <= open_price:
            return False
        
        # 몸통 비율 = (종가 - 시가) / (고가 - 시가)
        body_ratio = (close - open_price) / (high - open_price) if high > open_price else 0
        return body_ratio >= config.body_ratio_min


@dataclass
class ClosePositionCondition:
    """종가 위치 조건"""
    name: str = "종가 위치"
    enabled: bool = True
    close_pct: float = 0.95  # 고가 대비 최소 비율 (95%)
    description: str = "매도 압력 여부 판단 (종가 ≥ 당일 고가의 %)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'ClosePositionCondition') -> bool:
        """종가 위치 조건 검증"""
        if not config.enabled:
            return True
        
        close = row.get('close', 0)
        high = row.get('high', 1)
        
        return (close / high) >= config.close_pct


@dataclass
class TrendCondition:
    """단기 추세 조건"""
    name: str = "단기 추세"
    enabled: bool = True
    ma_period: int = 5        # 이동평균 기간
    ma_enabled: bool = True   # 이동평균 사용
    breakout_period: int = 20 # 고점 기간
    breakout_enabled: bool = True  # 고점 돌파 사용
    description: str = "추세 유무 판단 (5일 이동평균 위 OR 20일 고점 돌파)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'TrendCondition') -> bool:
        """추세 조건 검증 (OR 조건)"""
        if not config.enabled:
            return True
        
        results = []
        
        # MA 확인
        if config.ma_enabled:
            ma = row.get(f'ma{config.ma_period}', 0)
            close = row.get('close', 0)
            results.append(close >= ma)
        
        # 고점 돌파 확인
        if config.breakout_enabled:
            high_max = row.get(f'high_max_{config.breakout_period}', 0)
            high = row.get('high', 0)
            results.append(high >= high_max)
        
        # 활성화된 조건 중 하나라도 만족하면 True
        return any(results) if results else True


@dataclass
class VolatilityCondition:
    """변동성 필터"""
    name: str = "변동성 필터"
    enabled: bool = True
    min_volatility: float = 0.02  # 최소 2% 변동률
    period: int = 10  # 평균 일변동률 계산 기간
    description: str = "구조적 수익 가능성 판단 (최근 평균 일변동률 ≥ %)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'VolatilityCondition') -> bool:
        """변동성 조건 검증"""
        if not config.enabled:
            return True
        
        volatility = row.get('volatility', 0)
        return volatility >= config.min_volatility


@dataclass
class SizeCondition:
    """종목 규모 조건"""
    name: str = "종목 규모"
    enabled: bool = True
    market_cap_min: int = 100_000_000_000  # 1000억원
    market_cap_max: int = 1_000_000_000_000  # 1조
    price_min: int = 3_000
    price_max: int = 50_000
    description: str = "유동성 및 리스크 관리 (시가총액 1000억~1조, 주가 3000~50000원)"

    @staticmethod
    def validate(row: Dict[str, Any], config: 'SizeCondition') -> bool:
        """종목 규모 조건 검증"""
        if not config.enabled:
            return True
        
        market_cap = row.get('market_cap', 0)
        price = row.get('close', 0)
        
        cap_ok = config.market_cap_min <= market_cap <= config.market_cap_max
        price_ok = config.price_min <= price <= config.price_max
        
        return cap_ok and price_ok


@dataclass
class BacktestConfig:
    """백테스트 설정"""
    initial_capital: int = 10_000_000  # 초기자산 1000만원
    take_profit: float = 0.01  # 익절 +1%
    stop_loss: float = -0.01   # 손절 -1%
    equal_weight: bool = True  # 동일 비중 투자
    use_next_day_open: bool = False  # 다음날 시가로 매수 (False = 당일 종가)


@dataclass
class SearchConfig:
    """검색기 전체 설정"""
    volume: VolumeCondition = field(default_factory=VolumeCondition)
    candle: CandleCondition = field(default_factory=CandleCondition)
    close: ClosePositionCondition = field(default_factory=ClosePositionCondition)
    trend: TrendCondition = field(default_factory=TrendCondition)
    volatility: VolatilityCondition = field(default_factory=VolatilityCondition)
    size: SizeCondition = field(default_factory=SizeCondition)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    
    # 점수화 설정
    scoring_enabled: bool = False
    weights: Dict[str, float] = field(default_factory=lambda: {
        "volume": 0.15,
        "candle": 0.15,
        "close": 0.15,
        "trend": 0.30,
        "volatility": 0.15,
        "size": 0.10,
    })
    
    def get_conditions_dict(self) -> Dict[str, Any]:
        """모든 조건을 딕셔너리로 반환"""
        return {
            ConditionType.VOLUME.value: self.volume,
            ConditionType.CANDLE.value: self.candle,
            ConditionType.CLOSE_POSITION.value: self.close,
            ConditionType.TREND.value: self.trend,
            ConditionType.VOLATILITY.value: self.volatility,
            ConditionType.SIZE.value: self.size,
        }
    
    def get_enabled_conditions(self) -> Dict[str, Any]:
        """활성화된 조건만 반환"""
        return {k: v for k, v in self.get_conditions_dict().items() if v.enabled}


# 기본 설정 인스턴스
DEFAULT_CONFIG = SearchConfig()
