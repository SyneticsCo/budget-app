from budget.core import add_transaction


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
