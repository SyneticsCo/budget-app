"""Minimal FastAPI app for the budget web page."""

from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from budget.core import load_transactions_from_csv

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


def render_transactions_table(transactions: list[dict[str, object]]) -> str:
    """Render transactions as an HTML table."""
    if not transactions:
        return "<p>표시할 거래가 없습니다.</p>"
    rows = "".join(
        _transaction_row(transaction)
        for transaction in transactions
    )
    return f"<table>{_transaction_header()}<tbody>{rows}</tbody></table>"


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
