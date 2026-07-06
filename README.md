# budget-app

CSV 파일 기반의 가계부 데이터를 처리하고 FastAPI 웹 화면으로 확인하는 Python
프로젝트입니다. 거래 내역을 불러오고, 잔액 계산, 카테고리 필터링, 월별
수입/지출/순이익 요약, 웹 기반 거래 조회와 검색을 수행합니다.

## 주요 기능

### 코어 기능

- 거래 내역 추가
- 전체 잔액 계산
- 카테고리별 거래 필터링
- CSV 파일에서 거래 내역 로드
- 월별 수입, 지출, 순이익 요약
- UTF-8 BOM 포함 CSV 헤더 처리

### 웹 UI 기능

- `/`: 가계부 웹 홈
- `/transactions`: CSV 거래 목록 조회
- `/summary`: 연도별 월별 요약 차트와 표 조회
- `/search`: 날짜 범위와 카테고리 기반 거래 검색
- 거래 목록과 월별 요약 페이지네이션
- HTML 값 이스케이프와 날짜 입력 검증
- 5,000건 대용량 CSV 샘플 데이터 처리

## 프로젝트 구조

```text
budget-app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── static/
│   │   └── styles.css
│   └── templates/
│       ├── base.html
│       ├── content.html
│       └── home.html
├── budget/
│   ├── __init__.py
│   └── core.py
├── data/
│   ├── step1_transactions.csv
│   ├── step2_transactions.csv
│   ├── step3_transactions.csv
│   └── step4_large_transactions.csv
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_main.py
│   └── test_performance.py
├── requirements.txt
└── README.md
```

## 요구 사항

- Python 3.11 이상 권장
- pip

## 설치

```bash
cd /home/synetics/Dev/budget-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 웹 UI 실행

```bash
uvicorn app.main:create_app --factory --reload
```

브라우저에서 `http://127.0.0.1:8000`으로 접속합니다.

웹 UI는 기본적으로 `data/step4_large_transactions.csv` 파일을 사용합니다.

### 웹 경로

| 경로 | 설명 |
| --- | --- |
| `/` | 홈 화면 |
| `/transactions` | 최근 거래 목록 |
| `/summary` | 월별 수입, 지출, 잔액 요약과 연도별 차트 |
| `/search` | 카테고리, 시작일자, 종료일자로 거래 검색 |

검색 예시는 다음과 같습니다.

```text
http://127.0.0.1:8000/search?category=교통&start=2026-01-01&end=2026-06-30
```

## 코어 API 사용 예시

```python
from pathlib import Path

from budget.core import (
    filter_by_category,
    get_balance,
    load_transactions_from_csv,
    monthly_summary,
)

transactions = load_transactions_from_csv(Path("data/step1_transactions.csv"))

balance = get_balance(transactions)
food_transactions = filter_by_category(transactions, "식비")
summary = monthly_summary(transactions)

print(balance)
print(food_transactions)
print(summary)
```

## CSV 형식

거래 내역 CSV는 다음 헤더를 사용합니다.

```csv
date,type,category,description,amount,memo
2026-01-05,지출,식비,점심식사,-12000,
2026-01-07,수입,급여,월급,3500000,1월급여
```

### 필드 설명

| 필드 | 설명 | 예시 |
| --- | --- | --- |
| `date` | 거래 날짜 | `2026-01-05` |
| `type` | 거래 유형 | `수입`, `지출` |
| `category` | 거래 카테고리 | `식비`, `급여`, `교통` |
| `description` | 거래 설명 | `점심식사` |
| `amount` | 거래 금액 | 수입은 양수, 지출은 음수 |
| `memo` | 추가 메모 | `카드결제` |

## 샘플 데이터

| 파일 | 설명 |
| --- | --- |
| `data/step1_transactions.csv` | 기본 기능 테스트용 10건 샘플 |
| `data/step2_transactions.csv` | 카테고리와 월별 계산 테스트용 확장 샘플 |
| `data/step3_transactions.csv` | 중간 규모 샘플 |
| `data/step4_large_transactions.csv` | 웹 UI와 성능 테스트용 5,000건 샘플 |

## 테스트

```bash
pytest
```

커버리지 기준을 포함해 실행하려면 다음 명령을 사용합니다.

```bash
pytest --cov=budget --cov-report=term-missing --cov-fail-under=70
```

## 품질 검사

```bash
radon cc -s budget tests
xenon --max-absolute B --max-modules B --max-average B budget tests
flake8 budget tests
```

웹 앱까지 포함해 검사하려면 다음처럼 `app`도 대상에 포함합니다.

```bash
radon cc -s app budget tests
xenon --max-absolute B --max-modules B --max-average B app budget tests
flake8 app budget tests
```

## 개발 규칙

- 모든 함수와 메서드는 타입 힌트를 작성합니다.
- 함수는 20줄 이하로 유지합니다.
- 순환 복잡도는 5 이하로 유지합니다.
- 기능 구현 전 테스트를 먼저 작성하는 TDD 방식을 따릅니다.
