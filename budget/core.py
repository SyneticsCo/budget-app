"""Core budget transaction operations."""

import csv
from pathlib import Path


def add_transaction(
    transactions: list[dict[str, object]],
    transaction: dict[str, object],
) -> list[dict[str, object]]:
    """Add a transaction and return the updated list."""
    required_fields = (
        "date",
        "type",
        "category",
        "description",
        "amount",
        "memo",
    )
    stored_transaction = {
        field: transaction[field]
        for field in required_fields
    }
    return [*transactions, stored_transaction]


def get_balance(transactions: list[dict[str, object]]) -> float:
    """Return the sum of income and expense amounts."""
    return sum(float(transaction["amount"]) for transaction in transactions)


def filter_by_category(
    transactions: list[dict[str, object]],
    category: str,
) -> list[dict[str, object]]:
    """Return transactions matching the category case-insensitively."""
    target_category = category.casefold()
    return [
        dict(transaction)
        for transaction in transactions
        if str(transaction["category"]).casefold() == target_category
    ]


def load_transactions_from_csv(csv_path: Path) -> list[dict[str, object]]:
    """Load transactions from a UTF-8 BOM-compatible CSV file."""
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        return [_convert_csv_row(row) for row in csv.DictReader(file)]


def monthly_summary(
    transactions: list[dict[str, object]],
) -> dict[str, dict[str, int]]:
    """Calculate monthly income, expense, and net totals."""
    summary: dict[str, dict[str, int]] = {}
    for transaction in transactions:
        month = _get_transaction_month(transaction)
        summary.setdefault(month, _empty_month_summary())
        _add_amount_to_summary(summary[month], int(transaction["amount"]))
    return summary


def _get_transaction_month(transaction: dict[str, object]) -> str:
    """Return the YYYY-MM month for a transaction."""
    return str(transaction["date"])[:7]


def _empty_month_summary() -> dict[str, int]:
    """Return an empty monthly summary bucket."""
    return {"income": 0, "expense": 0, "net": 0}


def _add_amount_to_summary(summary: dict[str, int], amount: int) -> None:
    """Add an amount to income, expense, and net totals."""
    if amount >= 0:
        summary["income"] += amount
    else:
        summary["expense"] += amount
    summary["net"] += amount


def _convert_csv_row(row: dict[str, str]) -> dict[str, object]:
    """Convert a CSV row to a transaction dictionary."""
    return {
        "date": row["date"],
        "type": row["type"],
        "category": row["category"],
        "description": row["description"],
        "amount": int(row["amount"]),
        "memo": row["memo"],
    }
