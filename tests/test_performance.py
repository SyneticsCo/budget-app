from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import TypeVar

import pytest

from app.main import (
    _filter_transactions,
    render_summary_table,
    render_transactions_table,
)
from budget.core import load_transactions_from_csv, monthly_summary

LARGE_CSV = Path("data/step4_large_transactions.csv")
MAX_LOAD_SECONDS = 1.0
MAX_PATH_SECONDS = 1.0
MAX_TOTAL_PATH_SECONDS = 2.0

T = TypeVar("T")
MeasuredTransactions = tuple[list[dict[str, object]], float]


@pytest.fixture(scope="session")
def large_transactions_with_load_time() -> MeasuredTransactions:
    return _measure(lambda: load_transactions_from_csv(LARGE_CSV))


def test_large_csv_loads_within_ci_budget(
    large_transactions_with_load_time: MeasuredTransactions,
) -> None:
    transactions, load_seconds = large_transactions_with_load_time

    assert len(transactions) == 5000
    assert load_seconds < MAX_LOAD_SECONDS, _format_load_result(load_seconds)


def test_large_csv_web_paths_complete_within_ci_budget(
    large_transactions_with_load_time: MeasuredTransactions,
) -> None:
    transactions, _load_seconds = large_transactions_with_load_time
    durations = _measure_web_paths(transactions)
    details = _format_path_results(durations)

    assert _slowest_path(durations) == "list", details
    assert max(durations.values()) < MAX_PATH_SECONDS, details
    assert sum(durations.values()) < MAX_TOTAL_PATH_SECONDS


def _measure_web_paths(
    transactions: list[dict[str, object]],
) -> dict[str, float]:
    """Measure list, summary, and search rendering paths."""
    return {
        "list": _measure(lambda: render_transactions_table(transactions))[1],
        "summary": _measure(lambda: _render_summary(transactions))[1],
        "search": _measure(lambda: _render_search(transactions))[1],
    }


def _render_summary(transactions: list[dict[str, object]]) -> str:
    """Render monthly summary for performance measurement."""
    return render_summary_table(monthly_summary(transactions))


def _render_search(transactions: list[dict[str, object]]) -> str:
    """Render filtered transactions for performance measurement."""
    filtered = _filter_transactions(
        transactions,
        "2026-01-01",
        "2026-06-30",
        "식비",
    )
    return render_transactions_table(filtered)


def _measure(action: Callable[[], T]) -> tuple[T, float]:
    """Return an action result and elapsed seconds."""
    start_time = perf_counter()
    result = action()
    return result, perf_counter() - start_time


def _slowest_path(durations: dict[str, float]) -> str:
    """Return the slowest measured web path."""
    return max(durations, key=durations.get)


def _format_load_result(load_seconds: float) -> str:
    """Return a diagnostic load performance message."""
    return f"load={load_seconds:.4f}s limit={MAX_LOAD_SECONDS:.4f}s"


def _format_path_results(durations: dict[str, float]) -> str:
    """Return diagnostic path performance details."""
    parts = [f"{name}={seconds:.4f}s" for name, seconds in durations.items()]
    return f"slowest={_slowest_path(durations)} " + " ".join(parts)
