import pytest
import datetime
from types import SimpleNamespace
from app.models import User, Portfolio, PortfolioSecurity, Transaction
from app.service.alpha_vantage_client import get_company_name, get_price_data

@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username = "testuser", firstname = "John", lastname = "Doe", balance = 5000)
    db_session.add(user)

    db_session.flush()
    
    portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
    portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
    db_session.add_all([portfolio1, portfolio2])
    
    db_session.flush()

    portfoliosecurity = PortfolioSecurity(portfolio_id = portfolio1.id, username = user.username, role = "viewer")
    db_session.add(portfoliosecurity)
    
    db_session.flush()

    db_session.commit()
    return {
        "user": user,
        "portfolio1": portfolio1,
        "portfolio2": portfolio2
    }


def test_get_all_portfolios(client, setup, monkeypatch, mock_alpha_vantage):
    portfolio1 = setup["portfolio1"]
    portfolio2 = setup["portfolio2"]

    # Monkeypatch the service layer to return the portfolios created by the setup fixture
    monkeypatch.setattr("app.service.portfolio_service.get_all_portfolios",lambda: [portfolio1, portfolio2])

    response = client.get("/portfolios/")
    assert response.status_code == 200

    data = response.get_json()

    #assert isinstance(data, list)

    assert data[0]["id"] == portfolio1.id
    assert data[0]["name"] == portfolio1.name

    assert data[1]["id"] == portfolio2.id
    assert data[1]["name"] == portfolio2.name


def test_get_portfolio_by_id(client, setup, monkeypatch, mock_alpha_vantage):
    portfolio = setup["portfolio1"]

    # Monkeypatch service layer
    monkeypatch.setattr("app.service.portfolio_service.get_portfolio_by_id", lambda portfolio_id: portfolio)

    response = client.get(f"/portfolios/{portfolio.id}")
    assert response.status_code == 200

    data = response.get_json()

    assert data["id"] == portfolio.id
    assert data["name"] == portfolio.name
    assert data["description"] == portfolio.description


def test_get_portfolios_by_user(client, setup, monkeypatch, mock_alpha_vantage):
    user = setup["user"]
    portfolio1 = setup["portfolio1"]
    portfolio2 = setup["portfolio2"]

    monkeypatch.setattr("app.service.portfolio_service.get_portfolios_by_user", lambda user: [portfolio1, portfolio2])

    response = client.get(f"/portfolios/user/{user.username}")
    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["id"] == portfolio1.id
    assert data[0]["name"] == portfolio1.name
    assert data[0]["description"] == portfolio1.description

    assert data[1]["id"] == portfolio2.id
    assert data[1]["name"] == portfolio2.name
    assert data[1]["description"] == portfolio2.description



def test_create_portfolio_success(client, setup, monkeypatch, mock_alpha_vantage):
    user = setup["user"]
    monkeypatch.setattr("app.service.user_service.get_user_by_username", lambda username: user)
    monkeypatch.setattr("app.service.portfolio_service.create_portfolio", lambda name, description, user: 123)

    input = {"username": user.username, "name": "New Portfolio", "description": "Created via test"}

    response = client.post("/portfolios/", json= input)

    assert response.status_code == 201

    data = response.get_json()
    assert data["message"] == "Portfolio created successfully"
    assert data["portfolio_id"] == 123


def test_delete_portfolio_success(client, setup, monkeypatch, mock_alpha_vantage):
    user = setup["user"]
    portfolio = setup["portfolio1"]
    portfolio.owner = user.username
    monkeypatch.setattr(
        "app.service.portfolio_service.get_portfolio_by_id",
        lambda portfolio_id: portfolio
    )

    monkeypatch.setattr(
        "app.service.portfolio_service.delete_portfolio",
        lambda portfolio_id: None
    )

    response = client.delete(f"/portfolios/{portfolio.id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Portfolio deleted successfully"


def test_get_portfolio_transactions_success(client, setup, monkeypatch, mock_alpha_vantage):
    user = setup["user"]
    portfolio = setup["portfolio1"]
    tx1 = Transaction(transaction_id=1,username=user.username,portfolio_id=portfolio.id,ticker="AAPL",transaction_type="buy",quantity=10,price=150.0,date_time=datetime.datetime(2021, 6, 30))
    tx2 = Transaction(transaction_id=2,username=user.username,portfolio_id=portfolio.id,ticker="TSLA",transaction_type="sell",quantity=5,price=700.0,date_time=datetime.datetime(2020, 1, 1))

    monkeypatch.setattr(
        "app.service.transaction_service.get_transactions_by_portfolio_id",
        lambda portfolio_id: [tx1, tx2]
    )

    response = client.get(f"/portfolios/{portfolio.id}/transactions")

    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

    assert data[0]["transaction_id"] == 1
    assert data[0]["ticker"] == "AAPL"
    assert data[0]["quantity"] == 10
    assert data[0]["price"] == 150.0
    assert data[0]["transaction_type"] == "buy"

    assert data[1]["transaction_id"] == 2
    assert data[1]["ticker"] == "TSLA"
    assert data[1]["quantity"] == 5
    assert data[1]["price"] == 700.0
    assert data[1]["transaction_type"] == "sell"



def test_add_portfolio_security_success(client, setup, monkeypatch, mock_alpha_vantage):
    portfolio = setup["portfolio1"]
    called = {}

    def mock_create_portfolio_security(portfolio_id, username, role):
        called["portfolio_id"] = portfolio_id
        called["username"] = username
        called["role"] = role

    monkeypatch.setattr(
        "app.service.portfolio_service.create_portfolio_security",
        mock_create_portfolio_security
    )

    input = {
        "username": "viewer_user",
        "role": "viewer"
    }

    response = client.post(
        f"/portfolios/{portfolio.id}/security",
        json=input
    )

    assert response.status_code == 200
    assert response.get_json() == "Portfolio security updated successfully"

    assert called["portfolio_id"] == portfolio.id
    assert called["username"] == "viewer_user"
    assert called["role"] == "viewer"

def test_get_company_name_cache_hit(monkeypatch):
    class FakeCache:
        def get(self, key):
            return "Microsoft Corporation"

    monkeypatch.setattr(
        "app.service.alpha_vantage_client._get_cache",
        lambda: FakeCache()
    )

    result = get_company_name("MSFT")

    assert result == "Microsoft Corporation"

def test_get_price_data_cache_hit(monkeypatch, app):
    from app.service.alpha_vantage_client import get_price_data
    class FakeCache:
        def get(self, key):
            return {"price": 123.45, "date": "2024-01-01"}

    monkeypatch.setattr(
        "app.service.alpha_vantage_client._get_cache",
        lambda: FakeCache()
    )

    with app.app_context():
        result = get_price_data("AAPL")

    assert result == {"price": 123.45, "date": "2024-01-01"}

def test_get_price_data_returns_none(monkeypatch, app):
    class FakeCache:
        def get(self, key):
            return None
        def set(self, key, value, timeout=None):
            pass

    class FakeResponse:
        def json(self):
            return {}

    def fake_requests_get(url, params):
        return FakeResponse()

    monkeypatch.setattr("app.service.alpha_vantage_client._get_cache", lambda: FakeCache())
    monkeypatch.setattr("app.service.alpha_vantage_client._get_api_key", lambda: "demo")
    monkeypatch.setattr("app.service.alpha_vantage_client.requests.get", fake_requests_get)

    with app.app_context():
        result = get_price_data("AAPL")

    assert result is None

def test_get_company_name_returns_none(monkeypatch, app):
    class FakeCache:
        def get(self, key):
            return None
        def set(self, key, value, timeout=None):
            pass

    class FakeResponse:
        def json(self):
            return {"bestMatches": []}  
        def raise_for_status(self):
            pass

    def fake_requests_get(url, params, timeout):
        return FakeResponse()

    monkeypatch.setattr("app.service.alpha_vantage_client._get_cache", lambda: FakeCache())
    monkeypatch.setattr("app.service.alpha_vantage_client._get_api_key", lambda: "demo")
    monkeypatch.setattr("app.service.alpha_vantage_client.requests.get", fake_requests_get)

    with app.app_context():
        result = get_company_name("MSFT")

    assert result is None



def test_grant_portfolio_access_success(app, client, monkeypatch):
    class FakePortfolio:
        owner_username = "owner123"

    monkeypatch.setattr(
        "app.routes.portfolio_routes.portfolio_service.get_portfolio_by_id",
        lambda pid: FakePortfolio()
    )

    called = {"grant": False}

    def fake_grant_access(pid, username, role):
        called["grant"] = True

    monkeypatch.setattr("app.routes.portfolio_routes.portfolio_service.grant_access", fake_grant_access)
    monkeypatch.setattr("app.routes.portfolio_routes.g", SimpleNamespace(user={"username": "owner123"}))

    response = client.post(
        "/portfolios/1/access",
        json={"username": "bob", "role": "viewer"}
    )

    assert response.status_code == 200
    assert called["grant"] is True



def test_revoke_portfolio_access_success(app, client, monkeypatch):
    class FakePortfolio:
        owner_username = "owner123"

    monkeypatch.setattr("app.routes.portfolio_routes.portfolio_service.get_portfolio_by_id", lambda pid: FakePortfolio())
    called = {"revoke": False}

    def fake_revoke_access(pid, username):
        called["revoke"] = True
        return True

    monkeypatch.setattr("app.routes.portfolio_routes.portfolio_service.revoke_access", fake_revoke_access)
    monkeypatch.setattr("app.routes.portfolio_routes.g", SimpleNamespace(user={"username": "owner123"}))

    response = client.delete("/portfolios/1/access/bob")

    assert response.status_code == 200
    assert called["revoke"] is True


