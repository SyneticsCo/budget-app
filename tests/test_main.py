from app.main import app, home


def test_home_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/" in paths


def test_home_page_shows_budget_web_title() -> None:
    response = home()

    assert "가계부 웹" in response
    assert "<html lang=\"ko\">" in response
