"""Minimal FastAPI app for the budget web page."""

from datetime import date
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from budget.core import (
    filter_by_category,
    load_transactions_from_csv,
    monthly_summary,
)

TRANSACTIONS_CSV = Path("data/step4_large_transactions.csv")
APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"
TEMPLATE_DIR = APP_DIR / "templates"
TEMPLATES = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    web_app = FastAPI(title="가계부 웹")
    web_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    web_app.add_api_route("/", home, response_class=HTMLResponse)
    web_app.add_api_route(
        "/transactions",
        transactions_page,
        response_class=HTMLResponse,
    )
    web_app.add_api_route(
        "/summary",
        summary_page,
        response_class=HTMLResponse,
    )
    web_app.add_api_route("/search", search_page, response_class=HTMLResponse)
    return web_app


def home() -> str:
    """Return the local budget web home page."""
    return _render_template("home.html", {"title": "가계부 웹"})


def transactions_page() -> str:
    """Return a page with recent transactions."""
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    return _page("최근 거래", render_transactions_table(transactions))


def summary_page() -> str:
    """Return a page with monthly summary totals."""
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    summary = monthly_summary(transactions)
    return _page("월별 요약", render_summary_table(summary))


def search_page(
    start: str | None = None,
    end: str | None = None,
    category: str | None = None,
) -> str:
    """Return a filtered transaction search page."""
    start = _clean_filter_value(start)
    end = _clean_filter_value(end)
    category = _clean_filter_value(category)
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    categories = _category_options(transactions)
    form = _search_form(start, end, category, categories)
    error_message = _date_filter_error(start, end)
    if error_message:
        return _page("거래 검색", form + _error_message(error_message))
    filtered = _filter_transactions(transactions, start, end, category)
    return _page("거래 검색", form + render_transactions_table(filtered))


def render_transactions_table(transactions: list[dict[str, object]]) -> str:
    """Render transactions as an HTML table."""
    if not transactions:
        return "<p>표시할 거래가 없습니다.</p>"
    rows = "".join(
        _transaction_row(transaction)
        for transaction in transactions
    )
    return _table(_transaction_headers(), rows)


def render_summary_table(summary: dict[str, dict[str, int]]) -> str:
    """Render monthly summary values as an HTML table."""
    if not summary:
        return "<p>표시할 월별 요약이 없습니다.</p>"
    rows = "".join(
        _summary_row(month, values)
        for month, values in summary.items()
    )
    return _table(_summary_headers(), rows)


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


def _clean_filter_value(value: str | None) -> str | None:
    """Return None for empty form values."""
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


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
    format_error = _date_format_error(values)
    if format_error:
        return format_error
    return _date_range_error(start, end)


def _date_format_error(values: list[str]) -> str:
    """Return a date format error for invalid date strings."""
    try:
        for value in values:
            date.fromisoformat(value)
    except ValueError:
        return "날짜 형식은 YYYY-MM-DD여야 합니다."
    return ""


def _date_range_error(start: str | None, end: str | None) -> str:
    """Return an error when start date is after end date."""
    if _has_reversed_date_range(start, end):
        return "시작일자는 종료일자보다 늦을 수 없습니다."
    return ""


def _has_reversed_date_range(start: str | None, end: str | None) -> bool:
    """Return whether the date range is reversed."""
    if start is None or end is None:
        return False
    return date.fromisoformat(start) > date.fromisoformat(end)


def _page(title: str, content: str) -> str:
    """Wrap content in a minimal HTML page."""
    return _render_template(
        "content.html",
        {"title": title, "content": Markup(content)},
    )


def _search_form(
    start: str | None,
    end: str | None,
    category: str | None,
    categories: list[str],
) -> str:
    """Render the search filter form."""
    return f"""
    <form class="filter-form" method="get" action="/search">
      {_category_field(category, categories)}
      {_form_field("start", "시작일자", "date", start)}
      {_form_field("end", "종료일자", "date", end)}
      <div class="filter-actions">
        <button type="submit">검색</button>
        <a class="reset-link" href="/search">초기화</a>
      </div>
    </form>
    """


def _category_options(transactions: list[dict[str, object]]) -> list[str]:
    """Return sorted category options from transactions."""
    return sorted({
        str(transaction["category"])
        for transaction in transactions
    })


def _category_field(selected: str | None, categories: list[str]) -> str:
    """Render the category select field."""
    options = "".join(
        _category_option(category, selected)
        for category in categories
    )
    return f"""
    <label class="filter-field">
      <span>카테고리</span>
      <select name="category">
        <option value="">전체</option>
        {options}
      </select>
    </label>
    """


def _category_option(category: str, selected: str | None) -> str:
    """Render one category select option."""
    selected_attr = " selected" if category == selected else ""
    escaped_category = escape(category)
    return (
        f"<option value=\"{escaped_category}\"{selected_attr}>"
        f"{escaped_category}</option>"
    )


def _form_field(
    name: str,
    label: str,
    input_type: str,
    value: str | None,
) -> str:
    """Render one labeled form field."""
    return f"""
    <label class="filter-field">
      <span>{escape(label)}</span>
      <input
        type="{escape(input_type)}"
        name="{escape(name)}"
        value="{escape(value or "")}"
      >
    </label>
    """


def _error_message(message: str) -> str:
    """Render a search error message."""
    return f"<p class=\"error-message\">{escape(message)}</p>"


def _render_template(template_name: str, context: dict[str, object]) -> str:
    """Render a Jinja2 template."""
    return TEMPLATES.get_template(template_name).render(**context)


def _table(headers: list[str], rows: str) -> str:
    """Render a complete HTML table."""
    return f"<table>{_table_head(headers)}<tbody>{rows}</tbody></table>"


def _table_head(headers: list[str]) -> str:
    """Render an HTML table header."""
    cells = "".join(_header_cell(header) for header in headers)
    return f"<thead><tr>{cells}</tr></thead>"


def _header_cell(value: str) -> str:
    """Render an escaped table header cell."""
    return f"<th>{escape(value)}</th>"


def _row(cells: list[object]) -> str:
    """Render an HTML table row."""
    return f"<tr>{''.join(_cell(cell) for cell in cells)}</tr>"


def _cell(value: object) -> str:
    """Render an escaped table cell."""
    return f"<td>{escape(str(value))}</td>"


def _transaction_headers() -> list[str]:
    """Return transaction table headers."""
    return ["날짜", "유형", "카테고리", "설명", "금액", "메모"]


def _summary_headers() -> list[str]:
    """Return summary table headers."""
    return ["월", "수입", "지출", "잔액"]


def _summary_row(month: str, values: dict[str, int]) -> str:
    """Render one monthly summary row."""
    return _row([month, values["income"], values["expense"], values["net"]])


def _transaction_row(transaction: dict[str, object]) -> str:
    """Render one transaction row."""
    return _row([
        transaction["date"],
        transaction["type"],
        transaction["category"],
        transaction["description"],
        transaction["amount"],
        transaction["memo"],
    ])


app = create_app()
