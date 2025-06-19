import pytest
from flask import url_for, current_app
from models import User
from routes import main_bp
from bs4 import BeautifulSoup

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user(app, client, db_session):
    # 管理者ユーザー作成
    user = User(username='admin', email='admin@example.com', is_admin=True, is_active=True)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()

    # ログインページからCSRFトークンを取得
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

    # CSRFトークンを使ってログイン
    client.post(
        '/login',
        data={
            'username': user.username,
            'password': 'password',
            'csrf_token': csrf_token
        },
        follow_redirects=True
    )

    # セッション付きで返却
    return db_session.query(User).filter_by(username='admin').first()


class TestAdminCreateUser:

    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the create user page."""
        response = client.get('/admin/users/create')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_admin_create_user_success(self, client, admin_user, db_session):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/admin/users/create',
            data={
                'username': 'newuser',
                'password': 'password123',
                'email': 'newuser@example.com',
                'is_admin': 'y',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 302

    def test_admin_access_create_user_page(self, client, admin_user):
        response = client.get('/admin/users/create')
        assert response.status_code == 200
        assert '<title>新規ユーザー作成 - 受注管理システム</title>'.encode('utf-8') in response.data

    def test_admin_create_user_with_admin_privileges(self, client, admin_user, db_session):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/admin/users/create',
            data={
                'username': 'adminuser',
                'password': 'adminpass',
                'email': 'adminuser@example.com',
                'is_admin': 'y',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 302
        user = current_app.extensions['sqlalchemy'].session.query(User).filter_by(username='adminuser').first()
        assert user is not None
        assert user.is_admin

    def test_create_user_existing_username(self, client, admin_user, db_session):
        existing_user = User(username='existinguser', email='existing@example.com')
        existing_user.set_password('password123')
        db_session.add(existing_user)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/admin/users/create',
            data={
                'username': 'existinguser',
                'password': 'password123',
                'email': 'newemail@example.com',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 200
        assert 'ユーザー名は既に存在します。'.encode('utf-8') in response.data

    def test_create_user_existing_email(self, client, admin_user, db_session):
        existing_user = User(username='newuser', email='existing@example.com')
        existing_user.set_password('password123')
        db_session.add(existing_user)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/admin/users/create',
            data={
                'username': 'uniqueuser',
                'password': 'password123',
                'email': 'existing@example.com',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 200
        assert 'メールアドレスは既に存在します。'.encode('utf-8') in response.data

    def test_non_admin_access_create_user_page(self, client, authenticated_user):
        response = client.get('/admin/users/create')
        assert response.status_code == 302
        assert response.headers['Location'] == '/'