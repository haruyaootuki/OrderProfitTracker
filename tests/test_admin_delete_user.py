import pytest
from models import User
from flask_login import current_user
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

class TestAdminDeleteUser:
    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the create user page."""
        response = client.get('/admin/users/create')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_admin_successfully_deletes_user(self, client, admin_user, db_session):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            f'/admin/users/{user.id}/delete',
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 302
        assert db_session.query(User).get(user.id) is None

    def test_admin_receives_success_message(self, client, admin_user, db_session):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            f'/admin/users/{user.id}/delete',
            headers={'X-CSRFToken': csrf_token},
            follow_redirects=True
        )
        assert 'ユーザーが削除されました。'.encode('utf-8') in response.data

    def test_admin_redirected_after_deletion(self, client, admin_user, db_session):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            f'/admin/users/{user.id}/delete',
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 302
        assert response.location.endswith('/admin/users')

    def test_admin_deletes_non_existent_user(self, client, admin_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/admin/users/9999/delete',
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 404

    def test_database_error_during_deletion(self, client, admin_user, db_session, monkeypatch):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            f'/admin/users/{user.id}/delete',
            headers={'X-CSRFToken': csrf_token},
            follow_redirects=True
        )
        assert 'ユーザー削除中にエラーが発生しました'.encode('utf-8') in response.data

    def test_non_admin_attempts_deletion(self, client, authenticated_user, monkeypatch, app):
        monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', False)
        # 非管理者が削除を試みる
        response = client.post(
            '/admin/users/1/delete'
        )

        assert response.status_code ==302
        assert response.headers['Location'] == '/'
