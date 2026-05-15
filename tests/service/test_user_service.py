import pytest
import app.service.user_service as user_service
from app.models import User
from app.service.portfolio_service import create_portfolio

@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username="testuser", firstname="Test", lastname="User", balance=5000.0)
    admin = User(username = "admin", firstname = "Admin", lastname = "admin", balance = 1000.0)
    db_session.add(user)
    db_session.add(admin)

    db_session.flush() 

    db_session.commit()

    return {
        "user": user,
    }

def test_create_user(db_session):
    users_before = user_service.get_all_users()
    initial_count = len(users_before)
    user_service.create_user('test_user75', 'Test', 'User', 100.00)
    users_after = user_service.get_all_users()
    assert len(users_after) == initial_count + 1
    tests_user = user_service.get_user_by_username('test_user75')
    assert tests_user is not None
    assert tests_user.firstname == 'Test'
    assert tests_user.lastname == 'User'
    assert tests_user.balance == 100.00


def test_create_user_duplicate_username_raises():
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.create_user('testuser', 'Admin', 'User', 100.00)
    assert "Failed to create user due to error" in str(e.value)

def test_delete_user():
    users = user_service.get_all_users()
    initial_count = len(users)
    user_service.create_user('test_user77', 'Test', 'User', 150.00)
    users = user_service.get_all_users()
    assert len(users) == initial_count + 1
    user_service.delete_user('test_user77')
    users = user_service.get_all_users()
    assert len(users) == initial_count


def test_delete_admin_user_raises():
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.delete_user('admin')
    assert str(e.value) == "Cannot delete admin user"

def test_delete_nonexistent_user_raises():
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.delete_user('nonexistent_user')
    assert str(e.value) == "User with username nonexistent_user does not exist"

def test_delete_user_with_dependencies_raises(db_session):
    user_service.create_user('user1', 'Mr. User', 'Resu', 200.00)
    user1 = db_session.query(User).filter_by(username='user1').one()
    assert user1 is not None
    create_portfolio('Test Portfolio', 'Test Portfolio', user1)
    user1 = db_session.query(User).filter_by(username='user1').one()
    assert user1.portfolios is not None
    assert len(user1.portfolios) == 1
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.delete_user('user1')
    assert "due to existing dependencies" in str(e.value)

def test_update_user_balance(db_session):
    admin = user_service.get_user_by_username('admin')
    assert admin is not None
    assert admin.balance == 1000.00
    user_service.update_user_balance('admin', 500.00)
    user = db_session.query(User).filter_by(username='admin').one()
    assert user.balance == 500.00

def test_update_nonexistent_user_balance_raises():
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.update_user_balance('nonexistent_user', 300.00)
    assert "User with username nonexistent_user does not exist" in str(e.value)

def test_get_user_by_username():
    user = user_service.get_user_by_username('admin')
    assert user is not None
    assert user.username == 'admin'
    assert user.firstname == 'Admin'
    assert user.lastname == 'admin'

def test_get_user_by_username_nonexistent():
    user = user_service.get_user_by_username('nonexistent_user')
    assert user is None

def test_get_user_by_username_empty_raises():
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.get_user_by_username('')
    assert str(e.value) == "Failed to retrieve user due to error: Username cannot be empty"








