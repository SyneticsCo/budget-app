from app.main import (
    app,
    home,
    search_page,
    render_summary_table,
    render_transactions_table,
    summary_page,
    transactions_page,
)


def test_home_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/" in paths


def test_home_page_shows_budget_web_title() -> None:
    response = home()

    assert "가계부 웹" in response
    assert "<html lang=\"ko\">" in response


def test_transactions_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/transactions" in paths


def test_transactions_page_shows_csv_transactions() -> None:
    response = transactions_page()

    assert "최근 거래" in response
    assert "점심식사" in response
    assert "-12000" in response


def test_render_transactions_table_shows_empty_message() -> None:
    response = render_transactions_table([])

    assert "표시할 거래가 없습니다." in response
    assert "<table>" not in response


def test_summary_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/summary" in paths


def test_summary_page_shows_monthly_summary() -> None:
    response = summary_page()
    expected_values = ("월별 요약", "2026-01", "3525000", "-158300", "3366700")

    assert all(value in response for value in expected_values)


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
    assert "3500000" in response
    assert "-158300" in response
    assert "3341700" in response


def test_search_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/search" in paths


def test_search_page_without_filters_shows_all_transactions() -> None:
    response = search_page()

    assert "거래 검색" in response
    assert "점심식사" in response
    assert "중고 판매" in response


def test_search_page_filters_by_category() -> None:
    response = search_page(category="교통")

    assert "지하철" in response
    assert "택시" in response
    assert "점심식사" not in response


def test_search_page_filters_by_date_range() -> None:
    response = search_page(start="2026-01-20", end="2026-01-25")

    assert "택시" in response
    assert "병원 진료" in response
    assert "영화관" in response
    assert "점심식사" not in response


def test_search_page_returns_friendly_error_for_bad_date() -> None:
    response = search_page(start="2026/01/20")

    assert "날짜 형식은 YYYY-MM-DD여야 합니다." in response
    assert "<table>" not in response
