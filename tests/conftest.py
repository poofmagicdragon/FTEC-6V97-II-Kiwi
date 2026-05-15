from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator
from flask import Flask

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))



import app.db as db
import pytest
from app.auth import CognitoTokenValidator, required_auth
from app.service.alpha_vantage_client import SecurityQuote


from app.config import get_config
from app import create_app


@pytest.fixture(scope='session')
def app() -> Generator[Flask, None, None]:
    test_config = get_config("test")
    app = create_app(test_config)



    cognito_validator = CognitoTokenValidator(
        region = app.config['AWS_REGION'],
        user_pool_id = app.config['COGNITO_POOL_ID'],
        client_id=app.config['COGNITO_CLIENT_ID']
    )
    app.config['COGNITO_VALIDATOR'] = cognito_validator
    with app.app_context():
        
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        session = db.session
        yield session
        session.rollback()
        db.drop_all()





# mock authentication
@pytest.fixture(autouse=True)
def mock_authentication(app, monkeypatch):
    validator = app.config['COGNITO_VALIDATOR']

    # Mock token extraction
    monkeypatch.setattr('app.auth.get_token_from_header', lambda: 'token1234')

    # Mock token validation
    def mock_validate(token):
        return {
            'sub': 'user-abc',
            'username': 'testuser',
            'email': 'test@test.com',
            'exp': 1234567890,
            'token_use': 'access',
            'custom_field': 'custom_value'
        }

    if validator is not None:
        monkeypatch.setattr(validator, 'validate_token', mock_validate)

    # Mock get_user_info so it never calls Cognito
    monkeypatch.setattr(
        "app.auth.get_user_info",
        lambda token: {
            "username": "testuser",
            "attributes": {
                "given_name": "John",
                "family_name": "Doe"
            }
        }
    )


@pytest.fixture(scope = 'function')
def mock_alpha_vantage(app, monkeypatch):
    company_name = "Microsoft Corporation"
    price_data = {
        "open": 100.00,
        "high": 110.00,
        "low": 95.00,
        "close": 105.00,
        "volume": 123456
    }

    sample_quote = {
        "ticker": "MSFT",
        "price": price_data["close"],
        "issuer": company_name,
        "date": "2026-03-14"
    }

    def mock_get_company_name(ticker: str):
        return company_name
    
    def mock_get_price_data(ticker: str):
        return price_data
    
    def mock_get_quote(ticker:str):
        return SecurityQuote(ticker = sample_quote['ticker'], price = sample_quote['price'], issuer = sample_quote['issuer'], date = sample_quote['date'])

    monkeypatch.setattr("app.service.alpha_vantage_client.get_company_name", mock_get_company_name)
    
    monkeypatch.setattr("app.service.alpha_vantage_client.get_price_data", mock_get_price_data)
    
    monkeypatch.setattr("app.service.alpha_vantage_client.get_quote", mock_get_quote)




