from app.main import app, home, render_transactions_table, transactions_page


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
