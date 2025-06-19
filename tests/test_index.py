import pytest
from flask_login import current_user, login_user, logout_user
from routes import index
from flask import current_app

def test_authenticated_user_redirects_to_orders(client, test_user, app):
    # Simulate an authenticated user
    with app.test_request_context():
        login_user(test_user)
    with client:
        response = client.get('/')
        assert response.headers['Location'] == '/orders'
        assert response.status_code == 302

def test_unauthenticated_user_redirects_to_login(client, app):
    # Simulate an unauthenticated user
    with app.test_request_context():
        logout_user()
    with client:
        response = client.get('/')
        assert response.headers['Location'] == '/login'
        assert response.status_code == 302

def test_redirect_called_with_correct_url_authenticated(client, test_user, app):
    # Simulate an authenticated user
    with app.test_request_context():
        login_user(test_user)
    with client:
        response = client.get('/')
        assert response.headers['Location'] == '/orders'
        assert response.status_code == 302

def test_redirect_called_with_correct_url_unauthenticated(client, app):
    # Simulate an unauthenticated user
    with app.test_request_context():
        logout_user()
    with client:
        response = client.get('/')
        assert response.headers['Location'] == '/login'
        assert response.status_code == 302

def test_behavior_when_current_user_is_none(client, monkeypatch):
    # Simulate current_user being None
    with client:
        response = client.get('/')
        assert response.status_code == 302
        assert response.headers['Location'] == '/login'