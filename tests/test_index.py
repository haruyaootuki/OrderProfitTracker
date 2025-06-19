import pytest
from flask_login import current_user, login_user, logout_user
from routes import index

def test_authenticated_user_redirects_to_orders(client, test_user):
    # Simulate an authenticated user
    with client:
        login_user(test_user)
        response = client.get('/')
        assert response.headers['Location'] == '/orders'
        assert response.status_code == 302

def test_unauthenticated_user_redirects_to_login(client):
    # Simulate an unauthenticated user
    with client:
        logout_user()
        response = client.get('/')
        assert response.headers['Location'] == '/login'
        assert response.status_code == 302

def test_redirect_called_with_correct_url_authenticated(client, test_user):
    # Simulate an authenticated user
    with client:
        login_user(test_user)
        response = client.get('/')
        assert response.headers['Location'] == '/orders'
        assert response.status_code == 302

def test_redirect_called_with_correct_url_unauthenticated(client):
    # Simulate an unauthenticated user
    with client:
        logout_user()
        response = client.get('/')
        assert response.headers['Location'] == '/login'
        assert response.status_code == 302

def test_behavior_when_current_user_is_none(client, monkeypatch):
    # Simulate current_user being None
    with client:
        response = client.get('/')
        assert response.status_code == 302
        assert response.headers['Location'] == '/login'