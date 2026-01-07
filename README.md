# 📈 다음날 +1% 상승 가능성 검색기

**규칙 기반 국내 주식 단타 검색 도구**

다음 거래일에 +1% 이상 상승할 확률이 높은 국내 주식을 조건 기반으로 필터링하는 퀀트 검색 시스템입니다.

---

## 🎯 핵심 특징

### 예측 모델이 아닌 규칙 기반 시스템
- 기계학습이 아닌 명확한 기술적 지표와 거래량 기반 필터링
- 모든 조건을 UI에서 실시간 조절 가능
- 각 조건의 논리적 배경 이해 가능

### 6가지 검색 조건 (UI 조절 가능)

| # | 조건 | 기본값 | 설명 |
|---|------|--------|------|
| 1️⃣ | **거래대금 증가** | 20일 평균 × 2배 | 시장 참여 증가 여부 판단 |
| 2️⃣ | **양봉 조건** | 종가 > 시가 | 장 마감 기준 매수 우위 여부 |
| 3️⃣ | **종가 위치** | 고가의 95% 이상 | 매도 압력 여부 판단 |
| 4️⃣ | **단기 추세** | 5일 MA 위 OR 20일 고점 돌파 | 추세 유무 판단 |
| 5️⃣ | **변동성 필터** | 10일 평균 일변동률 ≥ 2% | 구조적 수익 가능성 판단 |
| 6️⃣ | **종목 규모** | 시가총액 1,000억~1조, 주가 3,000~50,000원 | 유동성 및 리스크 관리 |

### 매매 전략

```
매수: 당일 종가
익절: 다음날 고가가 +1% 이상 도달 시
손절: -1% (UI에서 조절 가능)
```

### 포트폴리오 관리
- 초기자산 설정 가능 (기본 1,000만원)
- 동일 비중 투자 (찾은 모든 종목에 균등 배분)
- 일별 수익률 추적 및 누적 자산 그래프 시각화

### 성과 지표
- **승률**: 수익 거래 비율
- **평균 수익률**: 거래당 평균 손익률
- **최대낙폭(MDD)**: 자산 최대 하락률
- **누적 수익률**: 전체 수익률

---

## 🚀 사용 방법

### 1. 설치

```bash
# 프로젝트 클론
cd searcher-korean-stock

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. 실행 방법

#### 방법 1: Streamlit UI (권장)
```bash
streamlit run app.py
```

또는

```bash
python run_streamlit.py
```

브라우저가 자동으로 열리며, `http://localhost:8501`에서 UI를 사용할 수 있습니다.

#### 방법 2: 명령줄 데모
```bash
python demo.py
```

---

## 📊 UI 가이드

### 좌측 사이드바: 조건 설정
- 6가지 검색 조건 각각 ON/OFF 가능
- 각 조건별 파라미터 실시간 조절
- 백테스트 설정 (초기자산, 익절, 손절)

### 메인 영역: 검색 및 결과
1. **검색 시작** 버튼 클릭
2. 조건 충족 종목 리스트 표시
3. 종목 선택하여 상세 조건 분석
4. **백테스트 실행** 버튼으로 성과 지표 확인

### 그래프 및 지표
- 누적 자산 변화 그래프
- 거래별 손익 테이블
- 성과 지표 카드 (승률, 수익률, MDD)

---

## 🏗️ 프로젝트 구조

```
searcher-korean-stock/
├── app.py                           # Streamlit 메인 애플리케이션
├── demo.py                          # 명령줄 데모 스크립트
├── run_streamlit.py                 # Streamlit 런처
├── requirements.txt                 # 의존성 패키지
├── README.md                        # 이 파일
└── src/searcher_korean_stock/
    ├── __init__.py
    ├── config.py                    # 조건 설정 (dataclass)
    ├── data_loader.py               # yfinance 기반 데이터 로더
    ├── engine.py                    # 검색 엔진 및 백테스트
    └── .cache/                      # 데이터 캐시 디렉토리
```

---

## 📝 주요 코드 구조

### 1. 조건 정의 (config.py)

모든 조건이 dataclass로 정의되어 있으며, 각 조건별로:
- `enabled`: 조건 활성화 여부
- `validate()`: 정적 메서드로 검증 로직 구현
- `description`: UI에 표시될 설명

### 2. 데이터 로드 (data_loader.py)

```python
loader = KoreanStockDataLoader()

# 여러 종목 데이터 로드
data = loader.prepare_data(days=60)

# 기술적 지표 자동 추가
# - 이동평균선 (5, 10, 20, 50일)
# - 거래량 비율
# - 변동성
# - 고점/저점 롤링
```

### 3. 검색 엔진 (engine.py)

```python
engine = DayTradeSearchEngine(config)

# 모든 종목 평가
results = engine.search(candidates_df, config)

# 조건별 상세 검증
conditions_met, conditions_detail, score = engine.evaluate_single_row(row, config)
```

### 4. 백테스트 (engine.py)

```python
backtest_engine = BacktestEngine(config)

# 후보 종목들에 대한 백테스트 실행
backtest_results = backtest_engine.simulate_trade(candidates, price_data)

# 반환: 거래 내역, 승률, 수익률, MDD 등
```

---

## 🔧 커스터마이제이션

### 조건 추가하기

`config.py`에 새로운 조건 클래스 추가:

```python
@dataclass
class MyCondition:
    name: str = "내 조건"
    enabled: bool = True
    parameter1: float = 0.5
    description: str = "..."
    
    @staticmethod
    def validate(row: Dict[str, Any], config: 'MyCondition') -> bool:
        if not config.enabled:
            return True
        # 조건 로직 구현
        return row['some_value'] > config.parameter1
```

### 데이터 소스 변경

`data_loader.py`의 `load_stock_data()` 메서드를 수정하여 다른 API 사용 가능:
- OpenDart API
- Naver Finance
- 로컬 CSV 파일
- 자체 DB

---

## ⚠️ 주의사항

1. **과거 성과 ≠ 미래 성과**: 백테스트 결과는 과거 데이터 기반이므로 미래 성과를 보장하지 않습니다.

2. **실제 거래 고려사항**:
   - 수수료 및 세금 미반영
   - 슬리피지 (실제 체결가 ≠ 예상가) 미반영
   - 유동성 부족으로 인한 체결 불가 가능성

3. **조건 최적화**:
   - 과거 데이터에 과적합되지 않도록 주의
   - 정기적으로 조건 성과 검증
   - 시장 환경 변화에 따른 조정 필요

4. **거래 중단**: 특정 조건에서 거래를 중단해야 합니다:
   - 베타 기간 (새로운 정책 도입 시)
   - 극단적 시장 변동성
   - 이벤트 리스크 (경제 지표, 공시 등)

---

## 📊 예제 결과

```
검색 결과 (최근 실행)
─────────────────────────────────────────────
종목           종목코드   현재가     조건충족   점수
─────────────────────────────────────────────
Samsung ...   005930.KS  70,000원   5/6       83.3%
SK Hynix      000660.KS  120,000원  4/6       66.7%
...

백테스트 결과
─────────────────────────────────────────────
총 거래: 25건
승 / 패: 18 / 7
승률: 72.0%
평균 수익률: +0.85%
총 수익률: +21.2%
최대낙폭: -3.2%
```

---

## 🔄 업데이트 계획

- [ ] 국내 주식 상장사 전체 대상 검색 (현재 10개 샘플)
- [ ] 실시간 데이터 업데이트 (Websocket)
- [ ] 추가 기술적 지표 (RSI, MACD, Bollinger Band 등)
- [ ] 포트폴리오 리스크 분석 (Beta, Correlation)
- [ ] 거래 자동화 (API 연동)

---

## 📧 문의 및 기여

버그 리포트 및 기능 요청은 이슈를 통해 제출해주세요.

---

## 📄 라이선스

MIT License

---

## 📚 참고 자료

- [yfinance 문서](https://github.com/ranaroussi/yfinance)
- [Streamlit 문서](https://docs.streamlit.io)
- [pandas 문서](https://pandas.pydata.org/docs)
- 기술적 분석 관련 자료

---

**⚠️ 면책사항**: 이 도구는 교육 목적으로 제공됩니다. 실제 투자 결정은 충분한 검토 후 스스로 판단하여 진행하세요.

**마지막 업데이트**: 2026년 1월 4일

## 모듈 구조
- `data_loader`: CSV/API 데이터 로딩 추상화
- `stock_filter`: 필수 조건 필터링
- `scorer`: 거래대금/가격 근접도/변동성/이동평균 정렬 기반 점수화
- `strategy`: 일별 상위 4개 후보 선정
- `backtester`: 다음날 시뮬레이션 실행
- `portfolio`: 자산·거래 기록 관리
- `visualizer`: 자산 곡선 및 성과 요약

## 실행 예시
```bash
python main.py
```

`data/sample_prices.csv`가 기본 입력으로 사용되며, 실행 시 조건 충족 종목, 거래 로그, 승률/평균 수익률/MDD, 월·주별 수익률을 출력하고 `equity_curve.png`를 저장합니다.

### 로컬 웹 UI 실행
```bash
python -m src.searcher_korean_stock.web_app
```

기본 포트 `8000`에서 웹 UI가 실행되며, 브라우저에서 `http://localhost:8000`으로 접속하면 스캐너 결과, 백테스트 요약, 누적 자산 곡선, 거래 로그를 확인할 수 있습니다. `data_path` 입력란에 CSV 경로를 바꿔 다른 데이터로 시각화할 수 있습니다.

## 데이터 포맷
CSV 컬럼 예시: `date,ticker,open,high,low,close,volume,amount,after_13_amount,after_13_low,after_13_high,market_cap`

## 의존성
- Python 3.10+
- pandas, numpy, matplotlib, flask

네트워크 제약으로 패키지 설치가 필요한 환경에서는 `pip install pandas numpy matplotlib flask`로 의존성을 설치한 뒤 실행하십시오.
