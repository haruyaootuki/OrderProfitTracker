import pytest
from models import User
from flask_login import login_user
from bs4 import BeautifulSoup

class TestLogin:

    def test_successful_login_with_valid_credentials(self, client, db_session):
        user = User(username='valid_user', email='valid_user@example.com', is_active=True)
        user.set_password('correct_password')
        db_session.add(user)
        db_session.commit()

        # Get CSRF token
        response = client.get('/login')
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

        response = client.post('/login', data={'username': 'valid_user', 'password': 'correct_password', 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert 'ログインしました' in response.data.decode('utf-8')

    def test_authenticated_user_redirect(self, client, db_session, app):
        user = User(username='authenticated_user', email='test@example.com', is_active=True)
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        with app.test_request_context():
            login_user(user)

        response = client.get('/login', follow_redirects=True)
        assert response.status_code == 200
        assert b'orders' in response.data

    def test_render_login_form_for_unauthenticated_user(self, client):
        response = client.get('/login')
        assert response.status_code == 200
        assert 'ログイン'.encode('utf-8') in response.data

    def test_login_fails_with_incorrect_password(self, client, db_session):
        user = User(username='user', email='test@example.com', is_active=True)
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        # Get CSRF token
        response = client.get('/login')
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

        response = client.post('/login', data={'username': 'user', 'password': 'wrong_password', 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert 'ユーザー名またはパスワードが正しくありません'.encode('utf-8') in response.data

    def test_login_fails_with_inactive_account(self, client, db_session):
        user = User(username='inactive_user', email='inactive@example.com', is_active=False)
        user.set_password('correct_password')
        db_session.add(user)
        db_session.commit()

        # Get CSRF token
        response = client.get('/login')
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

        response = client.post('/login', data={'username': 'inactive_user', 'password': 'correct_password', 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert 'ユーザー名またはパスワードが正しくありません'.encode('utf-8') in response.data

    def test_rate_limiting_on_login_attempts(self, client, db_session):
        user = User(username='rate_limit_user', email='rate_limit@example.com', is_active=True)
        user.set_password('correct_password')
        db_session.add(user)
        db_session.commit()

        # Get CSRF token once for all requests
        response = client.get('/login')
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

        for _ in range(6):
            response = client.post('/login', data={'username': 'rate_limit_user', 'password': 'wrong_password', 'csrf_token': csrf_token}, follow_redirects=True)

        assert response.status_code == 429
        assert b'Too Many Requests' in response.data