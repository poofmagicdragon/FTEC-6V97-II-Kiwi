from typing import List

from app.db import db
from app.models import Portfolio, User, PortfolioSecurity, Investment
from app.service import user_service


class UnsupportedPortfolioOperationError(Exception):
    pass


class PortfolioOperationError(Exception):
    pass


def create_portfolio(name: str, description: str, user: User) -> int:
    if not name or not description or not user:
        raise UnsupportedPortfolioOperationError(
            f'Invalid input[name: {name}, description: {description}, user: {user}]. Please try again.'
        )
    portfolio = Portfolio(name=name, description=description, user=user)
    try:
        db.session.add(portfolio)
        db.session.flush()
        return portfolio.id
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to create portfolio due to error: {str(e)}')


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).filter_by(owner=user.username).all()
        return portfolios
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_all_portfolios() -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).all()
        return portfolios
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_portfolio_by_id(portfolio_id: int) -> Portfolio | None:
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        return portfolio
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolio due to error: {str(e)}')


def delete_portfolio(portfolio_id: int):
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        holdings = db.session.query(Investment).filter_by(portfolio_id=portfolio_id).all()
        if len(holdings) > 0:
            raise UnsupportedPortfolioOperationError(f'Cannot delete a portfolio that still has holdings')
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist')
        db.session.delete(portfolio)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        raise e

def create_portfolio_security(portfolio_id: int, username: str, role: str, caller_user: str):
    portfolio = get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        raise UnsupportedPortfolioOperationError(f"No portfolio exists with ID {portfolio_id}")
    if portfolio.owner != caller_user:
        raise UnsupportedPortfolioOperationError(f'User {caller_user} is not authorized to set permission for portfolio with ID {portfolio_id}')
    if role not in ['manager', 'viewer']:
        raise UnsupportedPortfolioOperationError(f'Unsupported role: {role}. Supported Roles are : manager, viewer.')
    user = user_service.get_user_by_username(username)
    if user is None:
        raise UnsupportedPortfolioOperationError(f'User with username {username}does not exist')
    
    portfolio_security = PortfolioSecurity(portfolio_id = portfolio_id, username = username, role= role)
    db.session.add(portfolio_security)
    db.session.flush()

# def remove_portfolio_security():
#     # to be implemented
#     pass

def grant_access(portfolio_id, username, role):
    access = PortfolioSecurity(
        portfolio_id=portfolio_id,
        username=username,
        role=role
    )
    db.session.add(access)
    db.session.commit()
    return access


def revoke_access(portfolio_id, username):
    access = PortfolioSecurity.query.filter_by(
        portfolio_id=portfolio_id,
        username=username
    ).first()

    if not access:
        return None
    
    db.session.delete(access)
    return access


def user_has_role(username, portfolio_id, role):
    return PortfolioSecurity.query.filter_by(
        portfolio_id=portfolio_id,
        username=username,
        role=role
    ).first() is not None
