"""
다음날 +1% 상승 검색기 - Streamlit UI
"""
import sys
import os

# 절대 경로로 프로젝트 경로 설정
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_path = os.path.join(_current_dir, 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 패키지 import
from searcher_korean_stock.config import SearchConfig, VolumeCondition, CandleCondition, ClosePositionCondition, TrendCondition, VolatilityCondition, SizeCondition, BacktestConfig
from searcher_korean_stock.data_loader import loader
from searcher_korean_stock.engine import DayTradeSearchEngine, BacktestEngine
from searcher_korean_stock.tracker import tracker

# scheduler는 선택적
try:
    from searcher_korean_stock.scheduler import auto_tracker
    HAS_SCHEDULER = True
except (ImportError, ModuleNotFoundError):
    auto_tracker = None
    HAS_SCHEDULER = False


# 페이지 설정
st.set_page_config(
    page_title="다음날 +1% 상승 검색기",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 테마 설정
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# 테마별 색상 정의
THEMES = {
    'dark': {
        'bg_primary': '#0e1117',
        'bg_secondary': '#161b22',
        'text_primary': '#ffffff',
        'text_secondary': '#c9d1d9',
        'border': '#30363d',
        'metric_bg': '#1c2128',
        'input_bg': '#0d1117',
        'success_light': 'rgba(58, 150, 89, 0.15)',
        'success_dark': 'rgba(58, 150, 89, 1)',
        'error_light': 'rgba(248, 81, 73, 0.15)',
        'error_dark': 'rgba(248, 81, 73, 1)',
    },
    'light': {
        'bg_primary': '#ffffff',
        'bg_secondary': '#f0f2f6',
        'text_primary': '#000000',
        'text_secondary': '#262730',
        'border': '#d1d5da',
        'metric_bg': '#e8eef2',
        'input_bg': '#ffffff',
        'success_light': 'rgba(76, 175, 80, 0.1)',
        'success_dark': 'rgba(76, 175, 80, 1)',
        'error_light': 'rgba(244, 67, 54, 0.1)',
        'error_dark': 'rgba(244, 67, 54, 1)',
    }
}

theme = THEMES[st.session_state.theme]

# 스타일링
st.markdown(f"""
<style>
    * {{
        --bg-primary: {theme['bg_primary']} !important;
        --bg-secondary: {theme['bg_secondary']} !important;
        --text-primary: {theme['text_primary']} !important;
        --text-secondary: {theme['text_secondary']} !important;
        --border: {theme['border']} !important;
        --metric-bg: {theme['metric_bg']} !important;
    }}
    
    html {{
        background-color: {theme['bg_primary']} !important;
    }}
    
    body {{
        background-color: {theme['bg_primary']} !important;
        color: {theme['text_primary']} !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: {theme['bg_primary']} !important;
    }}
    
    [data-testid="stHeader"] {{
        background-color: {theme['bg_secondary']} !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {theme['bg_secondary']} !important;
    }}
    
    .main {{
        background-color: {theme['bg_primary']} !important;
        color: {theme['text_primary']} !important;
    }}
    
    .stMetric {{
        background-color: {theme['metric_bg']} !important;
        color: {theme['text_primary']} !important;
    }}
    
    .section-header {{
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme['bg_secondary']} !important;
        border-bottom: 2px solid {theme['border']} !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {theme['text_primary']} !important;
    }}
    
    .stDataFrame {{
        background-color: {theme['bg_secondary']} !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {theme['text_primary']} !important;
    }}
    
    p, label, span {{
        color: {theme['text_primary']} !important;
    }}
    
    input, textarea, select {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text_primary']} !important;
        border-color: {theme['border']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# 제목
st.title("📈 다음날 +1% 상승 가능성 검색기")
st.markdown("**규칙 기반 국내 주식 단타 검색 도구**")

# 세션 상태 초기화
if 'config' not in st.session_state:
    st.session_state.config = SearchConfig()

if 'search_results' not in st.session_state:
    st.session_state.search_results = None

if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# ============ 사이드바: 테마 설정 ============
col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown("### 🌙 테마")
with col2:
    theme_option = st.sidebar.radio("테마 선택", ["🌙 다크", "☀️ 라이트"], horizontal=True, label_visibility="collapsed", key="theme_radio_main")
    selected_theme = 'dark' if '다크' in theme_option else 'light'
    if st.session_state.get('theme') != selected_theme:
        st.session_state.theme = selected_theme
        st.rerun()

st.sidebar.markdown("---")

# ============ 사이드바: 조건 설정 ============
st.sidebar.markdown("### ⚙️ 검색 조건 설정")

# 1. 거래대금 증가
st.sidebar.markdown("#### 1️⃣ 거래대금 증가")
col1, col2 = st.sidebar.columns(2)
with col1:
    volume_enabled = st.checkbox("활성화", value=True, key="volume_enabled")
with col2:
    st.empty()

if volume_enabled:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        volume_multiplier = st.slider("배수", 1.0, 5.0, 2.0, 0.1, key="volume_multiplier")
    with col2:
        volume_period = st.number_input("기간(일)", 5, 50, 20, key="volume_period")
    st.sidebar.caption("당일 거래대금 ≥ 최근 평균의 배수")

st.session_state.config.volume.enabled = volume_enabled
st.session_state.config.volume.multiplier = volume_multiplier if volume_enabled else 1.0
st.session_state.config.volume.period = int(volume_period) if volume_enabled else 20

# 2. 양봉 조건
st.sidebar.markdown("#### 2️⃣ 양봉 조건")
candle_enabled = st.sidebar.checkbox("활성화", value=True, key="candle_enabled")
if candle_enabled:
    candle_body_ratio = st.sidebar.slider("몸통비율(%)", 0.0, 1.0, 0.3, 0.05, key="candle_body_ratio")
    st.sidebar.caption("종가 > 시가, 몸통 비율 조절 가능")
else:
    candle_body_ratio = 0.3

st.session_state.config.candle.enabled = candle_enabled
st.session_state.config.candle.body_ratio_min = candle_body_ratio

# 3. 종가 위치
st.sidebar.markdown("#### 3️⃣ 종가 위치")
close_enabled = st.sidebar.checkbox("활성화", value=True, key="close_enabled")
if close_enabled:
    close_pct = st.sidebar.slider("고가 대비(%)", 0.80, 1.00, 0.95, 0.01, key="close_pct")
    st.sidebar.caption("종가 ≥ 당일 고가의 %")
else:
    close_pct = 0.95

st.session_state.config.close.enabled = close_enabled
st.session_state.config.close.close_pct = close_pct

# 4. 단기 추세
st.sidebar.markdown("#### 4️⃣ 단기 추세")
trend_enabled = st.sidebar.checkbox("활성화", value=True, key="trend_enabled")
if trend_enabled:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        ma_period = st.number_input("MA기간", 3, 20, 5, key="ma_period")
    with col2:
        breakout_period = st.number_input("고점기간", 5, 50, 20, key="breakout_period")
    st.sidebar.caption("5일 MA 위 OR 20일 고점 돌파")
else:
    ma_period, breakout_period = 5, 20

st.session_state.config.trend.enabled = trend_enabled
st.session_state.config.trend.ma_period = int(ma_period)
st.session_state.config.trend.breakout_period = int(breakout_period)

# 5. 변동성 필터
st.sidebar.markdown("#### 5️⃣ 변동성 필터")
volatility_enabled = st.sidebar.checkbox("활성화", value=True, key="volatility_enabled")
if volatility_enabled:
    vol_threshold = st.sidebar.slider("최소 변동률(%)", 0.0, 0.05, 0.02, 0.001, key="vol_threshold")
    st.sidebar.caption("최근 10일 평균 일변동률 ≥ %")
else:
    vol_threshold = 0.02

st.session_state.config.volatility.enabled = volatility_enabled
st.session_state.config.volatility.min_volatility = vol_threshold

# 6. 종목 규모
st.sidebar.markdown("#### 6️⃣ 종목 규모")
size_enabled = st.sidebar.checkbox("활성화", value=True, key="size_enabled")
if size_enabled:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown("**시가총액(억원)**")
        market_cap_min = st.number_input("최소", 0, 100_000, 1_000, 100, key="market_cap_min")
        market_cap_max = st.number_input("최대", 1_000, 1_000_000, 10_000, 1000, key="market_cap_max")
    with col2:
        st.markdown("**주가(원)**")
        price_min = st.number_input("최소", 0, 100_000, 3_000, 1000, key="price_min")
        price_max = st.number_input("최대", 1_000, 1_000_000, 50_000, 10000, key="price_max")
    st.sidebar.caption("유동성 및 리스크 관리")
else:
    market_cap_min, market_cap_max = 1_000, 10_000
    price_min, price_max = 3_000, 50_000

st.session_state.config.size.enabled = size_enabled
st.session_state.config.size.market_cap_min = market_cap_min * 100_000_000
st.session_state.config.size.market_cap_max = market_cap_max * 100_000_000
st.session_state.config.size.price_min = price_min
st.session_state.config.size.price_max = price_max

# 백테스트 설정
st.sidebar.markdown("### 💰 백테스트 설정")
initial_capital = st.sidebar.number_input("초기자산(원)", 1_000_000, 1_000_000_000, 10_000_000, 1_000_000, key="initial_capital")
take_profit = st.sidebar.slider("익절(%)", 0.0, 0.10, 0.01, 0.001, key="take_profit")
stop_loss = st.sidebar.slider("손절(%)", -0.10, 0.0, -0.01, 0.001, key="stop_loss")

st.session_state.config.backtest.initial_capital = initial_capital
st.session_state.config.backtest.take_profit = take_profit
st.session_state.config.backtest.stop_loss = stop_loss

# ============ 메인 영역 ============
main_col1, main_col2 = st.columns([3, 1])

with main_col2:
    st.markdown("### 🚀 검색 실행")
    if st.button("검색 시작", use_container_width=True):
        with st.spinner("데이터 로드 중..."):
            try:
                # 데이터 로드
                data = loader.prepare_data(days=60)
                
                # 오늘 데이터 추출
                candidates_df = loader.get_today_candidates()
                
                if candidates_df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    # 검색 실행
                    engine = DayTradeSearchEngine(st.session_state.config)
                    results = engine.search(candidates_df, st.session_state.config)
                    
                    # 조건 충족 종목만 필터링 (최소 3개 조건)
                    filtered_results = [r for r in results if r.conditions_met >= 3]
                    
                    st.session_state.search_results = filtered_results
                    st.session_state.backtest_data = data
                    
                    st.success(f"✅ 검색 완료: {len(filtered_results)}개 종목 발견")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

# ============ 검색 결과 ============
if st.session_state.search_results:
    with main_col1:
        st.markdown("### 📊 검색 결과")
        
        # 결과를 테이블로 표시
        results_data = []
        for r in st.session_state.search_results[:20]:  # 상위 20개
            results_data.append({
                '종목명': r.stock_name,
                '종목코드': r.ticker,
                '현재가': f"{r.close:,.0f}원",
                '다음고가': f"{r.next_high:,.0f}원" if r.next_high > 0 else "N/A",
                '조건충족': f"{r.conditions_met}/6",
                '점수': f"{r.score:.2%}"
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True)
        
        # 조건 상세 분석
        st.markdown("#### 🔍 조건 상세")
        selected_idx = st.selectbox(
            "상세 분석할 종목 선택",
            range(len(st.session_state.search_results)),
            format_func=lambda i: f"{st.session_state.search_results[i].stock_name} ({st.session_state.search_results[i].ticker})"
        )
        
        selected_result = st.session_state.search_results[selected_idx]
        
        # 조건 상세 분석 - 개선된 UI
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        condition_info = {
            'volume': ('거래대금 증가', '시장 참여 증가 여부'),
            'candle': ('양봉 조건', '장 마감 기준 매수 우위'),
            'close': ('종가 위치', '매도 압력 여부'),
            'trend': ('단기 추세', '추세 유무 판단'),
            'volatility': ('변동성 필터', '구조적 수익 가능성'),
            'size': ('종목 규모', '유동성 및 리스크 관리')
        }
        
        condition_keys = ['volume', 'candle', 'close', 'trend', 'volatility', 'size']
        
        for i, key in enumerate(condition_keys):
            col = [col1, col2, col3][i % 3]
            with col:
                result = selected_result.conditions_detail.get(key, False)
                name, desc = condition_info[key]
                
                # 조건 충족 여부에 따른 색상
                if result:
                    bg_color = theme['success_light']
                    status_text = "✅ 충족"
                    status_color = theme['success_dark']
                else:
                    bg_color = theme['error_light']
                    status_text = "❌ 불충족"
                    status_color = theme['error_dark']
                
                st.markdown(f"""
                <div style='background-color: {bg_color}; padding: 15px; border-radius: 8px; border-left: 4px solid {status_color};'>
                    <h4 style='margin: 0 0 8px 0; color: {theme['text_primary']};'>{name}</h4>
                    <p style='margin: 0 0 10px 0; color: {theme['text_secondary']}; font-size: 0.9rem;'>{desc}</p>
                    <div style='font-size: 1.3rem; font-weight: bold; color: {status_color};'>{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

# ============ 백테스트 ============
if st.session_state.search_results and st.session_state.backtest_data:
    st.markdown("---")
    st.markdown("### 📈 백테스트 결과")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("백테스트 실행", use_container_width=True):
            with st.spinner("백테스트 진행 중..."):
                try:
                    backtest_engine = BacktestEngine(st.session_state.config)
                    bt_results = backtest_engine.simulate_trade(
                        st.session_state.search_results,
                        st.session_state.backtest_data
                    )
                    st.session_state.backtest_results = bt_results
                    st.success("✅ 백테스트 완료")
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")
    
    if st.session_state.backtest_results:
        bt = st.session_state.backtest_results
        
        # 성과 지표
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("승률", f"{bt['win_rate']:.1%}", f"{bt['win_count']}/{bt['total_trades']}")
        with col2:
            st.metric("평균수익률", f"{bt['avg_return']:.2%}")
        with col3:
            st.metric("총수익률", f"{bt['total_return']:.2%}")
        with col4:
            st.metric("최대낙폭", f"{bt['mdd']:.2%}")
        
        # 자산 곡선 그래프
        st.markdown("#### 누적 자산 변화")
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(bt['daily_equity'], linewidth=2, color='#1f77b4', label='자산')
        ax.fill_between(range(len(bt['daily_equity'])), bt['daily_equity'], alpha=0.3, color='#1f77b4')
        ax.set_ylabel('자산(원)', fontsize=10)
        ax.set_xlabel('거래', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        
        # 거래 상세
        if bt['trades']:
            st.markdown("#### 📋 거래 내역")
            trades_data = []
            for t in bt['trades']:
                trades_data.append({
                    '종목': t['ticker'],
                    '매수가': f"{t['buy_price']:,.0f}원",
                    '매도가': f"{t['sell_price']:,.0f}원",
                    '수익률': f"{t['pnl_pct']:.2%}",
                    '손익': f"{t['pnl_amount']:+,.0f}원",
                    '결과': '✅ 수익' if t['win'] else '❌ 손실'
                })
            trades_df = pd.DataFrame(trades_data)
            st.dataframe(trades_df, use_container_width=True)

# ============ 추적 결과 탭 ============
st.markdown("---")
st.markdown("### 📊 검색 결과 추적")

tab1, tab2, tab3 = st.tabs(["📈 통계", "📋 히스토리", "📅 일별 요약"])

with tab1:
    stats = tracker.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>누적 검색</div>
            <div style='font-size: 2rem; font-weight: bold; color: #1f77b4;'>{stats['total_searches']}회</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>누적 종목</div>
            <div style='font-size: 2rem; font-weight: bold; color: #1f77b4;'>{stats['total_candidates']}개</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>달성 종목</div>
            <div style='font-size: 2rem; font-weight: bold; color: #4CAF50;'>{stats['total_achieved']}개</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>정확도</div>
            <div style='font-size: 2rem; font-weight: bold; color: #FF9800;'>{stats['accuracy_rate']:.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>평균 점수</div>
            <div style='font-size: 2rem; font-weight: bold; color: #2196F3;'>{stats['avg_score']:.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background-color: {theme['metric_bg']}; padding: 20px; border-radius: 10px; border: 1px solid {theme['border']}; text-align: center;'>
            <div style='font-size: 1.2rem; color: {theme['text_secondary']}; margin-bottom: 10px;'>평균 조건</div>
            <div style='font-size: 2rem; font-weight: bold; color: #9C27B0;'>{stats['avg_conditions']:.1f}/6</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("#### 검색 결과 상세")
    history_df = tracker.get_history_dataframe(limit=100)
    
    if not history_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.selectbox(
                "검색 날짜 선택",
                sorted(history_df['검색날짜'].unique(), reverse=True),
                key="tracking_date"
            )
        with col2:
            show_all = st.checkbox("모든 결과 표시", False)
        
        if selected_date:
            filtered_df = history_df[history_df['검색날짜'] == selected_date].copy()
            if not show_all:
                filtered_df = filtered_df[filtered_df['달성'] == '✅']
            
            filtered_df['매수가'] = filtered_df['매수가'].apply(lambda x: f"{x:,.0f}원")
            filtered_df['다음고가'] = filtered_df['다음고가'].apply(lambda x: f"{x:,.0f}원")
            filtered_df['수익률'] = filtered_df['수익률'].apply(lambda x: f"{x:.2%}")
            filtered_df['점수'] = filtered_df['점수'].apply(lambda x: f"{x:.1%}")
            
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    else:
        st.info("추적 결과가 없습니다.")

with tab3:
    st.markdown("#### 날짜별 요약")
    summary_df = tracker.get_date_summary()
    
    if not summary_df.empty:
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ============ 스케줄러 관리 ============
st.markdown("---")
st.markdown("### ⏰ 자동 추적 스케줄러")

if HAS_SCHEDULER and auto_tracker:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**검색 시간**: 15:50 (장 종료 10분 전)")
    with col2:
        st.write("**추적 시간**: 16:00 (장 종료 후)")
    with col3:
        if st.button("수동 검색 실행", use_container_width=True):
            with st.spinner("검색 진행 중..."):
                auto_tracker.run_daily_search()
                st.success("✅ 검색 완료")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("수동 추적 실행", use_container_width=True):
            with st.spinner("추적 진행 중..."):
                auto_tracker.run_daily_tracking()
                st.success("✅ 추적 완료")

    with col2:
        st.info("💡 **스케줄러 정보:**\n- 평일(월-금) 자동 실행\n- 백그라운드에서 실행\n- 상단의 수동 실행으로 즉시 테스트 가능")
else:
    st.warning("⚠️ **schedule 패키지가 설치되지 않았습니다.**\n\n자동 스케줄러를 사용하려면:\n```\npip install schedule\n```")


# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>⚠️ 면책사항: 이 도구는 교육 목적으로 제공됩니다. 실제 투자 결정은 충분한 검토 후 진행하세요.</p>
    <p>© 2026 Day Trade Search Engine</p>
</div>
""", unsafe_allow_html=True)
