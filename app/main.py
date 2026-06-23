"""Minimal FastAPI app for the budget web page."""

from datetime import date
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from budget.core import (
    filter_by_category,
    load_transactions_from_csv,
    monthly_summary,
)

app = FastAPI(title="가계부 웹")
TRANSACTIONS_CSV = Path("data/step1_transactions.csv")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Return the local budget web home page."""
    return """
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8">
        <title>가계부 웹</title>
      </head>
      <body>
        <main>
          <h1>가계부 웹</h1>
        </main>
      </body>
    </html>
    """


@app.get("/transactions", response_class=HTMLResponse)
def transactions_page() -> str:
    """Return a page with recent transactions."""
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    return _page("최근 거래", render_transactions_table(transactions))


@app.get("/summary", response_class=HTMLResponse)
def summary_page() -> str:
    """Return a page with monthly summary totals."""
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    summary = monthly_summary(transactions)
    return _page("월별 요약", render_summary_table(summary))


@app.get("/search", response_class=HTMLResponse)
def search_page(
    start: str | None = None,
    end: str | None = None,
    category: str | None = None,
) -> str:
    """Return a filtered transaction search page."""
    error_message = _date_filter_error(start, end)
    if error_message:
        return _page("거래 검색", f"<p>{escape(error_message)}</p>")
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    filtered = _filter_transactions(transactions, start, end, category)
    return _page("거래 검색", render_transactions_table(filtered))


def render_transactions_table(transactions: list[dict[str, object]]) -> str:
    """Render transactions as an HTML table."""
    if not transactions:
        return "<p>표시할 거래가 없습니다.</p>"
    rows = "".join(
        _transaction_row(transaction)
        for transaction in transactions
    )
    return f"<table>{_transaction_header()}<tbody>{rows}</tbody></table>"


def render_summary_table(summary: dict[str, dict[str, int]]) -> str:
    """Render monthly summary values as an HTML table."""
    if not summary:
        return "<p>표시할 월별 요약이 없습니다.</p>"
    rows = "".join(
        _summary_row(month, values)
        for month, values in summary.items()
    )
    return f"<table>{_summary_header()}<tbody>{rows}</tbody></table>"


def _filter_transactions(
    transactions: list[dict[str, object]],
    start: str | None,
    end: str | None,
    category: str | None,
) -> list[dict[str, object]]:
    """Filter transactions by optional date range and category."""
    filtered = _filter_transactions_by_date(transactions, start, end)
    if category:
        return filter_by_category(filtered, category)
    return filtered


def _filter_transactions_by_date(
    transactions: list[dict[str, object]],
    start: str | None,
    end: str | None,
) -> list[dict[str, object]]:
    """Filter transactions by optional start and end dates."""
    return [
        transaction
        for transaction in transactions
        if _is_in_date_range(transaction, start, end)
    ]


def _is_in_date_range(
    transaction: dict[str, object],
    start: str | None,
    end: str | None,
) -> bool:
    """Return whether a transaction date is within the given range."""
    transaction_date = date.fromisoformat(str(transaction["date"]))
    starts_after = (
        start is None
        or transaction_date >= date.fromisoformat(start)
    )
    ends_before = end is None or transaction_date <= date.fromisoformat(end)
    return starts_after and ends_before


def _date_filter_error(start: str | None, end: str | None) -> str:
    """Return a friendly date validation error message."""
    values = [value for value in (start, end) if value]
    return _date_format_error(values)


def _date_format_error(values: list[str]) -> str:
    """Return a date format error for invalid date strings."""
    try:
        for value in values:
            date.fromisoformat(value)
    except ValueError:
        return "날짜 형식은 YYYY-MM-DD여야 합니다."
    return ""


def _page(title: str, content: str) -> str:
    """Wrap content in a minimal HTML page."""
    return f"""
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8">
        <title>{escape(title)}</title>
      </head>
      <body>
        <main>
          <h1>{escape(title)}</h1>
          {content}
        </main>
      </body>
    </html>
    """


def _transaction_header() -> str:
    """Return the transaction table header."""
    return """
    <thead>
      <tr>
        <th>날짜</th>
        <th>유형</th>
        <th>카테고리</th>
        <th>설명</th>
        <th>금액</th>
        <th>메모</th>
      </tr>
    </thead>
    """


def _summary_header() -> str:
    """Return the summary table header."""
    return """
    <thead>
      <tr>
        <th>월</th>
        <th>수입</th>
        <th>지출</th>
        <th>잔액</th>
      </tr>
    </thead>
    """


def _summary_row(month: str, values: dict[str, int]) -> str:
    """Render one monthly summary row."""
    return f"""
    <tr>
      <td>{escape(month)}</td>
      <td>{escape(str(values["income"]))}</td>
      <td>{escape(str(values["expense"]))}</td>
      <td>{escape(str(values["net"]))}</td>
    </tr>
    """


def _transaction_row(transaction: dict[str, object]) -> str:
    """Render one transaction row."""
    return f"""
    <tr>
      <td>{escape(str(transaction["date"]))}</td>
      <td>{escape(str(transaction["type"]))}</td>
      <td>{escape(str(transaction["category"]))}</td>
      <td>{escape(str(transaction["description"]))}</td>
      <td>{escape(str(transaction["amount"]))}</td>
      <td>{escape(str(transaction["memo"]))}</td>
    </tr>
    """
