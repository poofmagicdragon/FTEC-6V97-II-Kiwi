import pytest
from flask import g

import app.service.user_service as user_service
import app.service.transaction_service as transaction_service
from app.models.User import User
from app.models.Transaction import Transaction

def test_get_users_success(client, monkeypatch):
    fake_users = [
        User(username="u1", firstname="A", lastname="B", balance=100),
        User(username="u2", firstname="C", lastname="D", balance=200),
    ]

    monkeypatch.setattr(user_service, "get_all_users", lambda: fake_users)
    response = client.get("/users/", headers={"Authorization": "Bearer test"})
    
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert data[0]["username"] == "u1"

def test_get_user_success(client, monkeypatch):
    fake_user = User(username="testuser", firstname="Test", lastname="User", balance=1000)

    monkeypatch.setattr(user_service,"get_user_by_username", lambda username: fake_user)
    response = client.get("/users/testuser", headers = {"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "testuser"

def test_get_user_not_found(client, monkeypatch):
    monkeypatch.setattr(user_service, "get_user_by_username", lambda username: None)

    response = client.get("/users/ghost", headers={"Authorization": "Bearer test"})
    assert response.status_code == 404

    data = response.get_json()
    assert "not found" in data["error"]

def test_create_user_success(client, monkeypatch):

    def fake_create_user(username, firstname, lastname, balance):
        return None

    monkeypatch.setattr(user_service, "create_user", fake_create_user)
    monkeypatch.setattr("app.db.session.commit", lambda: None)

    payload = {
        "username": "newuser",
        "firstname": "New",
        "lastname": "User",
        "balance": 500.00
    }

    response = client.post("/users/", json=payload, headers={"Authorization": "Bearer test"})
    assert response.status_code == 201

    data = response.get_json()
    assert data["message"] == "User created successfully"

def test_update_balance_success(client, monkeypatch):
    def fake_update_user_balance(username, new_balance):
        return None

    monkeypatch.setattr(user_service, "update_user_balance", fake_update_user_balance)
    monkeypatch.setattr("app.db.session.commit", lambda: None)

    payload = {"username": "testuser", "new_balance": 2000}

    response = client.put("/users/update-balance", json=payload, headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "User balance updated successfully"


def test_delete_user_success(client, monkeypatch):
    monkeypatch.setattr(user_service, "delete_user", lambda username: None)
    monkeypatch.setattr("app.db.session.commit", lambda: None)
    response = client.delete("/users/testuser", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200

    data = response.get_json()
    assert data["message"] == "User deleted successfully"

def test_get_user_transactions_empty(client, monkeypatch):
    monkeypatch.setattr(transaction_service, "get_transactions_by_user", lambda username: [])

    response = client.get("/users/testuser/transactions", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert response.get_json() == []