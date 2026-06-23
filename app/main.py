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
SUMMARY_PAGE_SIZE = 20
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


def summary_page(page: int = 1, year: str | None = None) -> str:
    """Return a page with monthly summary totals."""
    transactions = load_transactions_from_csv(TRANSACTIONS_CSV)
    summary = monthly_summary(transactions)
    content = render_summary_view(summary, page, year)
    return _page("월별 요약", content)


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


def render_summary_view(
    summary: dict[str, dict[str, int]],
    page: int = 1,
    year: str | None = None,
) -> str:
    """Render the summary chart and paginated table."""
    selected_year = _selected_summary_year(summary, year)
    return (
        render_summary_chart(summary, selected_year)
        + render_summary_table(summary, page=page, year=selected_year)
    )


def render_summary_table(
    summary: dict[str, dict[str, int]],
    page: int = 1,
    year: str | None = None,
) -> str:
    """Render monthly summary values as an HTML table."""
    if not summary:
        return "<p>표시할 월별 요약이 없습니다.</p>"
    items = _filtered_summary_items(summary, year)
    total_pages = _total_pages(len(items), SUMMARY_PAGE_SIZE)
    current_page = _normalize_page(page, total_pages)
    visible_items = _page_items(items, current_page, SUMMARY_PAGE_SIZE)
    rows = "".join(
        _summary_row(month, values)
        for month, values in visible_items
    )
    table = _table(_summary_headers(), rows)
    return table + _pagination(current_page, total_pages, year)


def render_summary_chart(
    summary: dict[str, dict[str, int]],
    year: str | None,
) -> str:
    """Render a yearly income and expense bar chart."""
    years = _summary_years(summary)
    chart_summary = _summary_for_year(summary, year)
    if not chart_summary:
        return _year_filter(years, year) + "<p>표시할 그래프가 없습니다.</p>"
    bars = "".join(
        _chart_month(month, values)
        for month, values in chart_summary
    )
    return (
        _year_filter(years, year)
        + f"<div class=\"summary-chart\">{bars}</div>"
    )


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


def _summary_items(
    summary: dict[str, dict[str, int]],
) -> list[tuple[str, dict[str, int]]]:
    """Return summary items sorted by month."""
    return sorted(summary.items())


def _filtered_summary_items(
    summary: dict[str, dict[str, int]],
    year: str | None,
) -> list[tuple[str, dict[str, int]]]:
    """Return summary items optionally filtered by year."""
    if year is None:
        return _summary_items(summary)
    return _summary_for_year(summary, year)


def _summary_years(summary: dict[str, dict[str, int]]) -> list[str]:
    """Return available years from summary keys."""
    return sorted({month[:4] for month in summary})


def _selected_summary_year(
    summary: dict[str, dict[str, int]],
    year: str | None,
) -> str | None:
    """Return the selected chart year."""
    years = _summary_years(summary)
    if year in years:
        return year
    return years[-1] if years else None


def _summary_for_year(
    summary: dict[str, dict[str, int]],
    year: str | None,
) -> list[tuple[str, dict[str, int]]]:
    """Return summary items for a selected year."""
    return [
        (month, values)
        for month, values in _summary_items(summary)
        if year is not None and month.startswith(year)
    ]


def _total_pages(item_count: int, page_size: int) -> int:
    """Return total page count."""
    return max(1, (item_count + page_size - 1) // page_size)


def _normalize_page(page: int, total_pages: int) -> int:
    """Clamp page into available range."""
    return min(max(page, 1), total_pages)


def _page_items(
    items: list[tuple[str, dict[str, int]]],
    page: int,
    page_size: int,
) -> list[tuple[str, dict[str, int]]]:
    """Return items for a page."""
    start_index = (page - 1) * page_size
    return items[start_index:start_index + page_size]


def _pagination(page: int, total_pages: int, year: str | None) -> str:
    """Render summary pagination."""
    if total_pages <= 1:
        return ""
    return (
        "<nav class=\"pagination\">"
        + _page_link("이전", page - 1, page > 1, year)
        + f"<span>페이지 {page} / {total_pages}</span>"
        + _page_link("다음", page + 1, page < total_pages, year)
        + "</nav>"
    )


def _page_link(label: str, page: int, enabled: bool, year: str | None) -> str:
    """Render one pagination link."""
    if not enabled:
        return f"<span class=\"page-link disabled\">{escape(label)}</span>"
    url = _summary_url(page, year)
    return f"<a class=\"page-link\" href=\"{url}\">{label}</a>"


def _summary_url(page: int, year: str | None) -> str:
    """Return a summary URL preserving filters."""
    year_query = f"&year={escape(year)}" if year else ""
    return f"/summary?page={page}{year_query}"


def _year_filter(years: list[str], selected_year: str | None) -> str:
    """Render chart year filter."""
    options = "".join(_year_option(year, selected_year) for year in years)
    return f"""
    <form class="year-filter" method="get" action="/summary">
      <label class="filter-field">
        <select name="year">{options}</select>
      </label>
      <button type="submit">적용</button>
    </form>
    """


def _year_option(year: str, selected_year: str | None) -> str:
    """Render one year select option."""
    selected_attr = " selected" if year == selected_year else ""
    escaped_year = escape(year)
    return (
        f"<option value=\"{escaped_year}\"{selected_attr}>"
        f"{escaped_year}</option>"
    )


def _chart_month(month: str, values: dict[str, int]) -> str:
    """Render one chart month with income and expense bars."""
    max_value = max(abs(values["income"]), abs(values["expense"]), 1)
    return f"""
    <div class="chart-month">
      <div class="bar-pair">
        {_chart_bar("income", values["income"], max_value)}
        {_chart_bar("expense", abs(values["expense"]), max_value)}
      </div>
      <span>{escape(month)}</span>
    </div>
    """


def _chart_bar(kind: str, amount: int, max_value: int) -> str:
    """Render one chart bar."""
    height = 24 + int((amount / max_value) * 116)
    label = _format_amount(amount)
    return (
        f"<div class=\"chart-bar {escape(kind)}\" "
        f"style=\"height: {height}px\" title=\"{label}\"></div>"
    )


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


def _cell(value: object) -> str:
    """Render an escaped table cell."""
    return f"<td>{escape(str(value))}</td>"


def _amount_cell(value: object) -> str:
    """Render a right-aligned amount table cell."""
    return f"<td class=\"amount-cell\">{escape(str(value))}</td>"


def _transaction_headers() -> list[str]:
    """Return transaction table headers."""
    return ["날짜", "유형", "카테고리", "설명", "금액", "메모"]


def _summary_headers() -> list[str]:
    """Return summary table headers."""
    return ["월", "수입", "지출", "잔액"]


def _summary_row(month: str, values: dict[str, int]) -> str:
    """Render one monthly summary row."""
    return (
        "<tr>"
        + _cell(month)
        + _amount_cell(_format_amount(values["income"]))
        + _amount_cell(_format_amount(values["expense"]))
        + _amount_cell(_format_amount(values["net"]))
        + "</tr>"
    )


def _transaction_row(transaction: dict[str, object]) -> str:
    """Render one transaction row."""
    return (
        "<tr>"
        + _cell(transaction["date"])
        + _cell(transaction["type"])
        + _cell(transaction["category"])
        + _cell(transaction["description"])
        + _amount_cell(_format_amount(transaction["amount"]))
        + _cell(transaction["memo"])
        + "</tr>"
    )


def _format_amount(value: object) -> str:
    """Format an amount with thousands separators."""
    return f"{int(value):,}"


app = create_app()
