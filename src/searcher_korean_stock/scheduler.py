"""
자동 추적 스케줄러
"""
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
import threading

try:
    import schedule
except ImportError as e:
    raise ImportError("schedule 패키지가 필요합니다. 설치: pip install schedule") from e

from .data_loader import loader
from .engine import DayTradeSearchEngine
from .config import SearchConfig, DEFAULT_CONFIG
from .tracker import tracker


class AutoTracker:
    """자동 추적 스케줄러"""
    
    def __init__(self, config: SearchConfig = None):
        """초기화"""
        self.config = config or DEFAULT_CONFIG
        self.engine = DayTradeSearchEngine(self.config)
        self.running = False
        self.scheduler_thread = None
    
    def run_daily_search(self) -> None:
        """매일 장 종료 후 검색 실행"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            print(f"[{today}] 검색 시작...")
            
            # 데이터 로드
            candidates_df = loader.get_today_candidates()
            
            if candidates_df.empty:
                print(f"[{today}] 데이터를 불러올 수 없습니다.")
                return
            
            # 검색 실행
            all_results = self.engine.search(candidates_df, self.config)
            filtered_results = [r for r in all_results if r.conditions_met >= 3]
            
            # 결과 저장
            tracker.add_search_results(today, filtered_results)
            print(f"[{today}] 검색 완료: {len(filtered_results)}개 종목 저장")
            
        except Exception as e:
            print(f"검색 중 오류: {e}")
    
    def run_daily_tracking(self) -> None:
        """매일 장 종료 후 이전 검색 결과 추적"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"[{yesterday}] 추적 시작...")
            
            # 어제 검색 결과가 있는지 확인
            yesterday_data = tracker.db.get(yesterday)
            if not yesterday_data or not yesterday_data.get("search_results"):
                print(f"[{yesterday}] 어제 검색 결과가 없습니다.")
                return
            
            # 데이터 로드 (60일)
            price_data = loader.prepare_data(days=60)
            
            # 추적 결과 업데이트
            tracker.update_tracking_results(yesterday, price_data)
            
            # 통계 계산
            yesterday_data = tracker.db.get(yesterday)
            tracking_results = yesterday_data.get("tracking_results", [])
            
            if tracking_results:
                achieved = sum(1 for r in tracking_results if r.get("achieved"))
                total = len(tracking_results)
                accuracy = achieved / total if total > 0 else 0
                print(f"[{yesterday}] 추적 완료: {achieved}/{total} 달성 ({accuracy:.1%})")
            
        except Exception as e:
            print(f"추적 중 오류: {e}")
    
    def schedule_jobs(self, search_time: str = "15:50", tracking_time: str = "16:00") -> None:
        """
        스케줄 설정
        
        Args:
            search_time: 검색 실행 시간 (HH:MM, 기본: 15:50 - 장 종료 10분 전)
            tracking_time: 추적 실행 시간 (HH:MM, 기본: 16:00 - 장 종료 후)
        """
        # 평일(월-금)만 실행
        schedule.every().monday.at(search_time).do(self.run_daily_search)
        schedule.every().tuesday.at(search_time).do(self.run_daily_search)
        schedule.every().wednesday.at(search_time).do(self.run_daily_search)
        schedule.every().thursday.at(search_time).do(self.run_daily_search)
        schedule.every().friday.at(search_time).do(self.run_daily_search)
        
        # 추적 (다음날 장 시작 전, 금요일 제외 - 월요일 16:00)
        schedule.every().monday.at(tracking_time).do(self.run_daily_tracking)
        schedule.every().tuesday.at(tracking_time).do(self.run_daily_tracking)
        schedule.every().wednesday.at(tracking_time).do(self.run_daily_tracking)
        schedule.every().thursday.at(tracking_time).do(self.run_daily_tracking)
        schedule.every().friday.at(tracking_time).do(self.run_daily_tracking)
    
    def start(self, search_time: str = "15:50", tracking_time: str = "16:00") -> None:
        """
        스케줄러 시작 (백그라운드 스레드)
        
        Args:
            search_time: 검색 시간
            tracking_time: 추적 시간
        """
        if self.running:
            print("스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        self.schedule_jobs(search_time, tracking_time)
        
        def scheduler_loop():
            print("📅 스케줄러 시작됨")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 확인
        
        self.scheduler_thread = threading.Thread(daemon=True, target=scheduler_loop)
        self.scheduler_thread.start()
    
    def stop(self) -> None:
        """스케줄러 중지"""
        self.running = False
        schedule.clear()
        print("📅 스케줄러 중지됨")
    
    def get_next_jobs(self) -> list:
        """다음 예정 작업 반환"""
        return schedule.jobs


# 전역 인스턴스
auto_tracker = AutoTracker()
