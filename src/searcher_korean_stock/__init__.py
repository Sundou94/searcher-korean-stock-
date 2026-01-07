"""
다음날 +1% 상승 검색기 패키지
"""
from .config import SearchConfig, BacktestConfig
from .data_loader import KoreanStockDataLoader, loader
from .engine import DayTradeSearchEngine, BacktestEngine
from .tracker import SearchTracker, tracker

# scheduler는 선택적 (schedule 패키지가 필요)
try:
    from .scheduler import AutoTracker, auto_tracker
except ImportError:
    AutoTracker = None
    auto_tracker = None

__version__ = "1.0.0"
__all__ = [
    "SearchConfig",
    "BacktestConfig", 
    "KoreanStockDataLoader",
    "loader",
    "DayTradeSearchEngine",
    "BacktestEngine",
    "SearchTracker",
    "tracker",
    "AutoTracker",
    "auto_tracker"
]
