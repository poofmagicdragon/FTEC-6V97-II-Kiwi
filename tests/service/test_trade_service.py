import pytest
from unittest.mock import patch, MagicMock
from app.models import User, Portfolio, Investment, Transaction
from app.service.trade_service import execute_purchase_order, liquidate_investment, TradeExecutionException


@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username="testuser", firstname="Test", lastname="User", balance=10000.0)
    db_session.add(user)
    db_session.commit()

    portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
    portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
    db_session.add_all([portfolio1, portfolio2])

    # The database needs to flush so that portfolio have an id
    db_session.flush() 

    portfolio1.investments.append(Investment(ticker="AAPL", quantity=10))

    db_session.commit()

    return {
        "user": user,
        "portfolio1": portfolio1,
        "portfolio2": portfolio2
    }



def test_execute_purchase_order(setup, db_session):
    user = setup["user"]
    portfolio = setup["portfolio1"]

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # simulate cache miss

    mock_quote = MagicMock()
    mock_quote.price = 200
    mock_quote.issuer = "Apple Inc."
    mock_quote.ticker = "AAPL"


    with patch("app.service.trade_service.get_quote", return_value = mock_quote):
            
        execute_purchase_order(portfolio_id = 1, ticker = "AAPL", quantity = 10)

        assert user.balance == 10000 - (10*200)
        
        inv = (db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker = "AAPL").first())
        assert inv.quantity == 20
        assert inv is not None

        txn = (db_session.query(Transaction).filter_by(portfolio_id=portfolio.id, ticker="AAPL").first())
        assert txn is not None
        assert txn.quantity == 10
        assert txn.price == 200
        assert txn.transaction_type == "BUY"
        assert txn.date_time is not None

def test_execute_purchase_order_insufficient_funds(setup, db_session):
    user = setup["user"]
    portfolio = setup["portfolio1"]

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # simulate cache miss

    mock_quote = MagicMock()
    mock_quote.price = 10000
    mock_quote.issuer = "Apple Inc."
    mock_quote.ticker = "AAPL"


    with patch("app.service.trade_service.get_quote", return_value = mock_quote):
        with patch("app.service.alpha_vantage_client._get_cache", return_value = mock_cache):    
            with pytest.raises(TradeExecutionException) as exc:
                execute_purchase_order(portfolio_id = 1, ticker = "AAPL", quantity = 10)
            assert "Insufficient" in str(exc.value)





# liqudate_investment tests



def test_liquidate_investment(setup, db_session):
    user = setup["user"]
    portfolio = setup["portfolio1"]

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # simulate cache miss

    mock_quote = MagicMock()
    mock_quote.price = 200
    mock_quote.issuer = "Apple Inc."
    mock_quote.ticker = "AAPL"


    with patch("app.service.trade_service.get_quote", return_value = mock_quote):
            
        liquidate_investment(portfolio_id = 1, ticker = "AAPL", quantity = 5, sale_price = mock_quote.price)

        assert user.balance == 10000 + (5*200)
        
        inv = (db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker = "AAPL").first())
        assert inv.quantity == 5
        assert inv is not None

        txn = (db_session.query(Transaction).filter_by(portfolio_id=portfolio.id, ticker="AAPL").first())
        assert txn is not None
        assert txn.quantity == 5
        assert txn.price == 200
        assert txn.transaction_type == "SELL"
        assert txn.date_time is not None                


def test_liquidate_investment_insufficient_quantity(setup, db_session):
    user = setup["user"]
    portfolio = setup["portfolio1"]

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # simulate cache miss

    mock_quote = MagicMock()
    mock_quote.price = 200
    mock_quote.issuer = "Apple Inc."
    mock_quote.ticker = "AAPL"


    with patch("app.service.trade_service.get_quote", return_value = mock_quote):
        with pytest.raises(TradeExecutionException) as exc:
            liquidate_investment(portfolio_id = 1, ticker = "AAPL", quantity = 15, sale_price = mock_quote.price)
        assert "Cannot liquidate" in str(exc.value)
 