"""Core budget transaction operations."""


def add_transaction(
    transactions: list[dict[str, object]],
    transaction: dict[str, object],
) -> list[dict[str, object]]:
    """Add a transaction to the transaction list and return the updated list."""
    required_fields = ("date", "type", "category", "description", "amount", "memo")
    stored_transaction = {field: transaction[field] for field in required_fields}
    return [*transactions, stored_transaction]


def get_balance(transactions: list[dict[str, object]]) -> float:
    """Return the sum of income and expense amounts."""
    return sum(float(transaction["amount"]) for transaction in transactions)
