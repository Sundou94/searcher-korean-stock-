# Korean Stock Next-Day +2% Scanner & Backtester

Python 기반 모듈로, 14:50 시점에 다음날 +2% 목표 도달 확률이 높은 종목을 선별하고 단타 전략을 백테스트합니다.

## 전략 요약
- **매수**: 당일 종가 매수
- **매도**: 다음날 고가가 매수가 대비 +2% 이상 도달 시 전량 매도
- **손절**: -1.5%
- **선정 시간**: 장 마감 전 14:00~15:00 조건 계산

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
