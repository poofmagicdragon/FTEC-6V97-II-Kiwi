import pytest

@pytest.fixture
def setup():
    class FakeUser:
        username = "testuser"

    class FakePortfolio:
        id = 1
        name = "Test Portfolio"
        description = "Test Desc"
        owner = "testuser"
        portfolio_securities = []

    return {
        "user": FakeUser(),
        "portfolio1": FakePortfolio(),
        "portfolio2": FakePortfolio(),
    }

def test_execute_purchase_order_success(client, setup, monkeypatch):
    portfolio = setup["portfolio1"]

    monkeypatch.setattr(
        "app.service.portfolio_service.get_portfolio_by_id",
        lambda pid: portfolio
    )

    called = {"executed": False}
    def fake_execute(portfolio_id, ticker, quantity):
        called["executed"] = True

    monkeypatch.setattr(
        "app.service.trade_service.execute_purchase_order",
        fake_execute
    )

    monkeypatch.setattr("app.db.session.commit", lambda: None)

    payload = {
        "portfolio_id": portfolio.id,
        "ticker": "AAPL",
        "quantity": 10
    }

    response = client.post("/trades/buy", json=payload)

    assert response.status_code == 201
    assert called["executed"] is True
    assert response.get_json()["message"] == "Purchase order executed successfully"




def test_liquidate_investment_success(client, setup, monkeypatch):
    portfolio = setup["portfolio1"]

    monkeypatch.setattr(
        "app.service.portfolio_service.get_portfolio_by_id",
        lambda pid: portfolio
    )

    called = {"executed": False}
    def fake_liquidate(portfolio_id, ticker, quantity, sale_price):
        called["executed"] = True

    monkeypatch.setattr(
        "app.service.trade_service.liquidate_investment",
        fake_liquidate
    )

    monkeypatch.setattr("app.db.session.commit", lambda: None)

    payload = {
        "portfolio_id": portfolio.id,
        "ticker": "AAPL",
        "quantity": 5,
        "sale_price": 150.00
    }

    response = client.post("/trades/sell", json=payload)

    assert response.status_code == 200
    assert called["executed"] is True

    data = response.get_json()
    assert data["message"] == "Investment liquidated successfully"
