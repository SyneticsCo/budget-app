from pathlib import Path

from budget.core import (
    add_transaction,
    filter_by_category,
    get_balance,
    load_transactions_from_csv,
    monthly_summary,
)


def test_add_transaction_increases_length() -> None:
    transactions: list[dict[str, object]] = []
    transaction: dict[str, object] = {
        "date": "2026-01-05",
        "type": "지출",
        "category": "식비",
        "description": "점심식사",
        "amount": -12000,
        "memo": "",
    }

    result = add_transaction(transactions, transaction)

    assert len(result) == 1


def test_add_transaction_stores_negative_expense_amount() -> None:
    transactions: list[dict[str, object]] = []
    transaction: dict[str, object] = {
        "date": "2026-01-10",
        "type": "지출",
        "category": "교통",
        "description": "지하철",
        "amount": -1500,
        "memo": "",
    }

    result = add_transaction(transactions, transaction)

    assert result[0]["amount"] == -1500


def test_add_transaction_stores_positive_income_amount() -> None:
    transactions: list[dict[str, object]] = []
    transaction: dict[str, object] = {
        "date": "2026-01-07",
        "type": "수입",
        "category": "급여",
        "description": "월급",
        "amount": 3500000,
        "memo": "1월급여",
    }

    result = add_transaction(transactions, transaction)

    assert result[0]["amount"] == 3500000


def test_add_transaction_allows_empty_description() -> None:
    transactions: list[dict[str, object]] = []
    transaction: dict[str, object] = {
        "date": "2026-01-28",
        "type": "기타수입",
        "category": "기타수입",
        "description": "",
        "amount": 25000,
        "memo": "중고마켓",
    }

    result = add_transaction(transactions, transaction)

    assert result[0]["description"] == ""


def test_get_balance_returns_zero_for_empty_transactions() -> None:
    transactions: list[dict[str, object]] = []

    result = get_balance(transactions)

    assert result == 0.0


def test_get_balance_sums_income_and_expense_amounts() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-02-01",
            "type": "수입",
            "category": "급여",
            "description": "월급",
            "amount": 4358625,
            "memo": "",
        },
        {
            "date": "2026-02-01",
            "type": "지출",
            "category": "여행",
            "description": "여행 경비",
            "amount": -651009,
            "memo": "카드결제",
        },
        {
            "date": "2026-02-15",
            "type": "지출",
            "category": "통신",
            "description": "케이블TV",
            "amount": -111988,
            "memo": "현금",
        },
    ]

    result = get_balance(transactions)

    assert result == 3595628.0


def test_get_balance_matches_step2_january_sample() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-01-04",
            "type": "지출",
            "category": "여행",
            "description": "항공권",
            "amount": -979796,
            "memo": "메모_3",
        },
        {
            "date": "2026-01-05",
            "type": "지출",
            "category": "의료",
            "description": "한의원",
            "amount": -65990,
            "memo": "카드결제",
        },
        {
            "date": "2026-01-15",
            "type": "수입",
            "category": "기타수입",
            "description": "중고 판매",
            "amount": 135541,
            "memo": "",
        },
    ]

    result = get_balance(transactions)

    assert result == -910245.0


def test_filter_by_category_matches_step2_category() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-01-04",
            "type": "지출",
            "category": "여행",
            "description": "항공권",
            "amount": -979796,
            "memo": "메모_3",
        },
        {
            "date": "2026-01-05",
            "type": "지출",
            "category": "의료",
            "description": "한의원",
            "amount": -65990,
            "memo": "카드결제",
        },
        {
            "date": "2026-02-01",
            "type": "지출",
            "category": "여행",
            "description": "여행 경비",
            "amount": -651009,
            "memo": "카드결제",
        },
    ]

    result = filter_by_category(transactions, "여행")

    assert len(result) == 2
    assert result[0]["description"] == "항공권"
    assert result[1]["description"] == "여행 경비"


def test_filter_by_category_matches_case_insensitively() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-02-01",
            "type": "수입",
            "category": "급여",
            "description": "월급",
            "amount": 4358625,
            "memo": "",
        },
    ]

    result = filter_by_category(transactions, "급여")

    assert result == transactions


def test_filter_by_category_returns_empty_for_missing_category() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-01-13",
            "type": "지출",
            "category": "교육",
            "description": "온라인 강의",
            "amount": -432554,
            "memo": "",
        },
    ]

    result = filter_by_category(transactions, "식비")

    assert result == []


def test_filter_by_category_returns_independent_result() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-01-10",
            "type": "지출",
            "category": "통신",
            "description": "인터넷 요금",
            "amount": -107684,
            "memo": "",
        },
    ]

    result = filter_by_category(transactions, "통신")
    result[0]["description"] = "수정된 설명"

    assert transactions[0]["description"] == "인터넷 요금"


def test_load_transactions_from_csv_reads_step1_rows() -> None:
    csv_path = Path("data/step1_transactions.csv")

    result = load_transactions_from_csv(csv_path)

    assert len(result) == 10


def test_load_transactions_from_csv_converts_amount_to_int() -> None:
    csv_path = Path("data/step1_transactions.csv")

    result = load_transactions_from_csv(csv_path)

    assert result[0]["amount"] == -12000
    assert isinstance(result[0]["amount"], int)


def test_load_transactions_from_csv_handles_utf8_sig_header() -> None:
    csv_path = Path("data/step1_transactions.csv")

    result = load_transactions_from_csv(csv_path)

    assert result[0] == {
        "date": "2026-01-05",
        "type": "지출",
        "category": "식비",
        "description": "점심식사",
        "amount": -12000,
        "memo": "",
    }


def test_monthly_summary_returns_empty_dict_for_empty_transactions() -> None:
    transactions: list[dict[str, object]] = []

    result = monthly_summary(transactions)

    assert result == {}


def test_monthly_summary_calculates_income_expense_and_net_by_month() -> None:
    transactions: list[dict[str, object]] = [
        {
            "date": "2026-01-07",
            "type": "수입",
            "category": "급여",
            "description": "월급",
            "amount": 3500000,
            "memo": "1월급여",
        },
        {
            "date": "2026-01-05",
            "type": "지출",
            "category": "식비",
            "description": "점심식사",
            "amount": -12000,
            "memo": "",
        },
        {
            "date": "2026-01-28",
            "type": "기타수입",
            "category": "기타수입",
            "description": "중고 판매",
            "amount": 25000,
            "memo": "중고마켓",
        },
        {
            "date": "2026-02-01",
            "type": "지출",
            "category": "여행",
            "description": "여행 경비",
            "amount": -651009,
            "memo": "카드결제",
        },
    ]

    result = monthly_summary(transactions)

    assert result == {
        "2026-01": {"income": 3525000, "expense": -12000, "net": 3513000},
        "2026-02": {"income": 0, "expense": -651009, "net": -651009},
    }


def test_load_transactions_from_csv_loads_step4_large_file() -> None:
    csv_path = Path("data/step4_large_transactions.csv")

    result = load_transactions_from_csv(csv_path)

    assert len(result) == 5000


def test_get_balance_returns_expected_step4_large_total() -> None:
    csv_path = Path("data/step4_large_transactions.csv")
    transactions = load_transactions_from_csv(csv_path)

    result = get_balance(transactions)

    assert result == 1134968783.0


def test_monthly_summary_handles_step4_large_month_range() -> None:
    csv_path = Path("data/step4_large_transactions.csv")
    transactions = load_transactions_from_csv(csv_path)

    result = monthly_summary(transactions)

    assert len(result) >= 65
    assert min(result) == "2020-01"
    assert max(result) == "2026-06"
