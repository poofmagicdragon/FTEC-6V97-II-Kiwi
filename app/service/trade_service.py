import datetime

from app.db import db
from app.models import Investment, Portfolio, Transaction
from app.service.alpha_vantage_client import get_quote

class TradeExecutionException(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


def execute_purchase_order(portfolio_id: int, ticker: str, quantity: int):
    """
    Execute a purchase order for a given portfolio, security ticker, and quantity.

    Args:
        portfolio_id (int): The ID of the portfolio.
        ticker (str): The ticker symbol of the security to purchase.
        quantity (int): The number of shares to purchase.

    Raises:
        TradeExecutionException: If there is an error during the trade execution.
        InsufficientFundsError: If the user has insufficient funds to complete the purchase.
    """

    if quantity == 0:
        raise TradeExecutionException(
            f'Please select a number of shares greater than 0 to buy'
        )
    
    if quantity < 0:
        raise TradeExecutionException(
            f'Please make quantity a positive number'
        )

    if portfolio_id is None or not ticker or not quantity or quantity <= 0:
        raise TradeExecutionException(
            f'Invalid purchase order parameters [portfolio_id={portfolio_id}, ticker={ticker}, quantity={quantity}]'
        )
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist.')
    user = portfolio.user
    if not user:
        raise TradeExecutionException(f'User associated with the portfolio ({portfolio_id}) does not exist.')

    # security = db.session.query(Security).filter_by(ticker=ticker).one_or_none()
    # if not security:
    #     raise TradeExecutionException(f'Security with ticker {ticker} does not exist.')
    # total_cost = security.price * quantity
    # if user.balance < total_cost:
    #     raise InsufficientFundsError('Insufficient funds to complete the purchase.')

    quote = get_quote(ticker)
    if not quote or quote.price is None:
        raise TradeExecutionException(f"Invalid ticker or price unavailable: {ticker}") 
    

    total_cost = quote.price * quantity
    if user.balance < total_cost:
        raise InsufficientFundsError('Insufficient funds to complete the purchase.')

    existing_investment = next((inv for inv in portfolio.investments if inv.ticker == ticker), None)
    if existing_investment:
        existing_investment.quantity += quantity
    else:
        portfolio.investments.append(Investment(ticker=ticker, quantity=quantity))

    user.balance -= total_cost
    db.session.add(
        Transaction(
            portfolio_id=portfolio.id,
            username=user.username,
            ticker=ticker,
            quantity=quantity,
            price=quote.price,
            transaction_type='BUY',
            date_time=datetime.datetime.now(),
        )
    )
    db.session.flush()


def liquidate_investment(portfolio_id: int, ticker: str, quantity: int, sale_price: float):
    """
    Liquidate shares of a security from a portfolio at a given sale price.

    Args:
        portfolio_id (int): The ID of the portfolio to sell from.
        ticker (str): The ticker symbol of the security to sell.
        quantity (int): The number of shares to sell.
        sale_price (float): The price per share to use for the sale.

    Raises:
        TradeExecutionException: If the portfolio, investment, or quantity is invalid,
            or if a database error occurs while recording the sale.
    """
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist')
    user = portfolio.user
    investment = next(
        (inv for inv in portfolio.investments if inv.ticker == ticker),
        None,
    )
    if quantity == 0:
        raise TradeExecutionException(
            f'Please select a number of shares greater than 0 to buy'
        )
    
    if quantity < 0:
        raise TradeExecutionException(
            f'Please make quantity a positive number'
        )
    if sale_price < 0:
        raise TradeExecutionException(
            f'Please make sale price a positive number'
        )
    if not investment:
        raise TradeExecutionException(
            f'No investment with ticker {ticker} exists in portfolio with id {portfolio_id}'
        )
    if investment.quantity < quantity:
        raise TradeExecutionException(
            f'Cannot liquidate {quantity} shares of {ticker}. Only {investment.quantity} shares available in portfolio'
        )
    total_proceeds = sale_price * quantity
    user.balance += total_proceeds
    if investment.quantity == quantity:
        db.session.delete(investment)
    else:
        investment.quantity -= quantity
    db.session.add(
        Transaction(
            portfolio_id=portfolio.id,
            username=user.username,
            ticker=ticker,
            quantity=quantity,
            price=sale_price,
            transaction_type='SELL',
            date_time=datetime.datetime.now(),
        )
    )
    db.session.flush()

