import pytest
# from flask import url_for
from flask_login import current_user
from routes import main_bp
from models import User
from flask import render_template as original_render_template
from bs4 import BeautifulSoup

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user(db_session):
    user = User(username='admin', email='admin@example.com', is_admin=True)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def non_admin_user(db_session):
    user = User(username='user', email='user@example.com', is_admin=False)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()
    return user

class TestAdminUsersPage:

    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the login page."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_admin_user_access(self, client, admin_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        client.post('/login', data={'username': 'admin', 'password': 'password', 'csrf_token': csrf_token}, follow_redirects=True)
        response = client.get('/admin/users')
        assert response.status_code == 200

    def test_render_admin_users_template(self, client, admin_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        client.post('/login', data={'username': 'admin', 'password': 'password', 'csrf_token': csrf_token}, follow_redirects=True)
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert '<title>ユーザー管理 - 受注管理システム</title>'.encode('utf-8') in response.data

    def test_non_admin_access_redirect(self, client, non_admin_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        client.post('/login', data={'username': 'user', 'password': 'password', 'csrf_token': csrf_token}, follow_redirects=True)
        response = client.get('/admin/users')
        assert response.status_code == 302
        assert '/' in response.headers['Location']

    def test_access_without_login(self, client):
        response = client.get('/admin/users')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_database_connection_failure(self, client, admin_user, monkeypatch, app):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        login_response = client.post('/login', data={'username': 'admin', 'password': 'password', 'csrf_token': csrf_token}, follow_redirects=True)
        assert login_response.status_code == 200

        class MockQueryResult:
            def all(self):
                raise Exception("Simulated database connection error")
            def filter_by(self, *args, **kwargs):
                return self
            def first(self):
                mock_user = User(username='admin', email='admin@example.com', is_admin=True)
                mock_user.set_password('password')
                return mock_user

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', lambda cls: MockQueryResult())

        response = client.get('/admin/users')
        assert response.status_code == 500
        assert '500 - サーバー内部エラー'.encode('utf-8') in response.data