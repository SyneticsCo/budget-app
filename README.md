# budget-app

CSV 파일 기반의 가계부 데이터를 처리하는 Python 프로젝트입니다. 거래 내역을
불러오고, 잔액 계산, 카테고리 필터링, 월별 수입/지출/순이익 요약을 수행합니다.

## 주요 기능

- 거래 내역 추가
- 전체 잔액 계산
- 카테고리별 거래 필터링
- CSV 파일에서 거래 내역 로드
- 월별 수입, 지출, 순이익 요약
- 대용량 CSV 샘플 데이터 처리 테스트

## 프로젝트 구조

```text
budget-app/
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
│   └── test_core.py
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

## 사용 예시

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

## 개발 규칙

- 모든 함수와 메서드는 타입 힌트를 작성합니다.
- 함수는 20줄 이하로 유지합니다.
- 순환 복잡도는 5 이하로 유지합니다.
- 기능 구현 전 테스트를 먼저 작성하는 TDD 방식을 따릅니다.
