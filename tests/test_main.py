from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from budget.core import load_transactions_from_csv
from app.main import (
    create_app,
    home,
    search_page,
    render_summary_chart,
    render_summary_table,
    render_transactions_table,
    summary_page,
    transactions_page,
)


@pytest.fixture(scope="session")
def loaded_transactions() -> list[dict[str, object]]:
    return load_transactions_from_csv(Path("data/step1_transactions.csv"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _route_paths(client: TestClient) -> set[str]:
    return {route.path for route in client.app.routes}


def test_home_route_is_registered(client: TestClient) -> None:
    paths = _route_paths(client)

    assert "/" in paths


def test_client_uses_isolated_app_instance(client: TestClient) -> None:
    other_client = TestClient(create_app())

    assert client.app is not other_client.app


def test_home_page_shows_budget_web_title() -> None:
    response = home()

    assert "가계부 웹" in response
    assert "<html lang=\"ko\">" in response


def test_home_page_uses_styled_template() -> None:
    response = home()

    assert "/static/styles.css" in response
    assert "app-shell" in response
    assert "nav-link" in response


def test_home_page_links_to_web_features() -> None:
    response = home()

    assert "href=\"/transactions\"" in response
    assert "href=\"/summary\"" in response
    assert "href=\"/search\"" in response


def test_transactions_route_is_registered(client: TestClient) -> None:
    paths = _route_paths(client)

    assert "/transactions" in paths


def test_transactions_page_shows_csv_transactions() -> None:
    response = transactions_page()

    assert "최근 거래" in response
    assert "점심식사" in response
    assert "-12,000" in response


def test_render_transactions_table_shows_loaded_transactions(
    loaded_transactions: list[dict[str, object]],
) -> None:
    response = render_transactions_table(loaded_transactions)

    assert "점심식사" in response
    assert "중고 판매" in response


def test_render_transactions_table_shows_empty_message() -> None:
    response = render_transactions_table([])

    assert "표시할 거래가 없습니다." in response
    assert "<table>" not in response


def test_render_transactions_table_escapes_html_values() -> None:
    transactions = [
        {
            "date": "2026-01-01",
            "type": "지출",
            "category": "<script>",
            "description": "테스트",
            "amount": -1000,
            "memo": "",
        },
    ]

    response = render_transactions_table(transactions)

    assert "&lt;script&gt;" in response
    assert "<script>" not in response


def test_render_transactions_table_formats_amount_with_commas() -> None:
    transactions = [
        {
            "date": "2026-01-01",
            "type": "수입",
            "category": "급여",
            "description": "월급",
            "amount": 3212756,
            "memo": "",
        },
    ]

    response = render_transactions_table(transactions)

    assert "3,212,756" in response


def test_render_transactions_table_marks_amount_cell() -> None:
    transactions = [
        {
            "date": "2026-01-01",
            "type": "수입",
            "category": "급여",
            "description": "월급",
            "amount": 3212756,
            "memo": "",
        },
    ]

    response = render_transactions_table(transactions)

    assert "class=\"amount-cell\">3,212,756" in response


def test_summary_route_is_registered(client: TestClient) -> None:
    paths = _route_paths(client)

    assert "/summary" in paths


def test_summary_page_shows_monthly_summary() -> None:
    response = summary_page(year="2020")
    expected_values = (
        "월별 요약",
        "2020-01",
        "37,502,538",
        "-11,873,710",
        "25,628,828",
    )

    assert all(value in response for value in expected_values)


def test_summary_page_uses_core_summary_values() -> None:
    response = summary_page(year="2020")

    assert "25,628,828" in response


def test_render_summary_table_shows_empty_message() -> None:
    response = render_summary_table({})

    assert "표시할 월별 요약이 없습니다." in response
    assert "<table>" not in response


def test_render_summary_table_displays_core_summary_values() -> None:
    summary = {
        "2026-01": {
            "income": 3500000,
            "expense": -158300,
            "net": 3341700,
        },
    }

    response = render_summary_table(summary)

    assert "2026-01" in response
    assert "3,500,000" in response
    assert "-158,300" in response
    assert "3,341,700" in response


def test_render_summary_table_marks_amount_cells() -> None:
    summary = {
        "2026-01": {
            "income": 3500000,
            "expense": -158300,
            "net": 3341700,
        },
    }

    response = render_summary_table(summary)

    assert "class=\"amount-cell\">3,500,000" in response
    assert "class=\"amount-cell\">-158,300" in response


def test_render_summary_table_shows_expected_headers() -> None:
    response = render_summary_table({
        "2026-01": {
            "income": 1,
            "expense": -1,
            "net": 0,
        },
    })

    assert "<th>월</th>" in response
    assert "<th>수입</th>" in response
    assert "<th>지출</th>" in response
    assert "<th>잔액</th>" in response


def test_render_summary_table_limits_rows_to_twenty() -> None:
    summary = {
        f"2026-{month:02d}": {"income": month, "expense": -month, "net": 0}
        for month in range(1, 22)
    }

    response = render_summary_table(summary)
    expected_values = ("2026-01", "2026-20", "페이지 1 / 2")

    assert all(value in response for value in expected_values)
    assert "2026-21" not in response


def test_render_summary_table_can_show_second_page() -> None:
    summary = {
        f"2026-{month:02d}": {"income": month, "expense": -month, "net": 0}
        for month in range(1, 22)
    }

    response = render_summary_table(summary, page=2)

    assert "2026-21" in response
    assert "href=\"/summary?page=1\"" in response


def test_summary_page_shows_year_filter_and_chart() -> None:
    response = summary_page(year="2026")

    assert "class=\"summary-chart\"" in response
    assert "name=\"year\"" in response
    assert "value=\"2026\" selected" in response
    assert "2026-01" in response


def test_render_summary_table_filters_rows_by_year() -> None:
    summary = {
        "2025-12": {"income": 1, "expense": -1, "net": 0},
        "2026-01": {"income": 2, "expense": -2, "net": 0},
    }

    response = render_summary_table(summary, year="2026")

    assert "2026-01" in response
    assert "2025-12" not in response


def test_render_summary_chart_shows_empty_message() -> None:
    response = render_summary_chart({}, None)

    assert "표시할 그래프가 없습니다." in response


def test_search_route_is_registered(client: TestClient) -> None:
    paths = _route_paths(client)

    assert "/search" in paths


def test_web_routes_allow_get_requests(client: TestClient) -> None:
    get_paths = {
        route.path
        for route in client.app.routes
        if "GET" in getattr(route, "methods", set())
    }

    assert {"/", "/transactions", "/summary", "/search"} <= get_paths


def test_search_page_without_filters_shows_all_transactions() -> None:
    response = search_page()

    assert "거래 검색" in response
    assert "점심식사" in response
    assert "중고 판매" in response


def test_search_page_shows_filter_form() -> None:
    response = search_page()
    expected_fields = (
        "method=\"get\"",
        "<select",
        "name=\"category\"",
        "name=\"start\"",
        "name=\"end\"",
    )

    assert all(field in response for field in expected_fields)


def test_search_page_category_filter_uses_select_options() -> None:
    response = search_page()

    assert "<option value=\"\">전체</option>" in response
    assert "<option value=\"교통\">" in response


def test_search_page_keeps_filter_values() -> None:
    response = search_page(
        start="2026-01-20",
        end="2026-01-25",
        category="교통",
    )

    assert "value=\"2026-01-20\"" in response
    assert "value=\"2026-01-25\"" in response
    assert "value=\"교통\"" in response


def test_search_page_filters_by_start_only() -> None:
    response = search_page(start="2026-01-20")

    assert "2026-01-20" in response
    assert "2020-01-01" not in response


def test_search_page_filters_by_end_only() -> None:
    response = search_page(end="2020-01-02")

    assert "2020-01-01" in response
    assert "2026-01-20" not in response


def test_search_page_returns_error_when_start_is_after_end() -> None:
    response = search_page(start="2026-01-25", end="2026-01-20")

    assert "시작일자는 종료일자보다 늦을 수 없습니다." in response
    assert "<table>" not in response


def test_search_page_filters_by_category() -> None:
    response = search_page(category="교통")

    assert "지하철" in response
    assert "택시" in response
    assert "점심식사" not in response


def test_search_page_treats_empty_dates_as_unset() -> None:
    response = search_page(start="", end="", category="교통")

    assert "거래 검색" in response
    assert "날짜 형식은 YYYY-MM-DD여야 합니다." not in response
    assert "<table>" in response


def test_search_page_filters_by_date_range() -> None:
    response = search_page(start="2026-01-20", end="2026-01-25")

    assert "2026-01-20" in response
    assert "중고 판매" in response
    assert "2020-01-01" not in response


def test_search_page_returns_friendly_error_for_bad_date() -> None:
    response = search_page(start="2026/01/20")

    assert "날짜 형식은 YYYY-MM-DD여야 합니다." in response
    assert "<table>" not in response
