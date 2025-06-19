import pytest
from flask import current_app
from flask_login import current_user
from models import User
from bs4 import BeautifulSoup
import logging

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

@pytest.fixture
def regular_user(db_session):
    user = User(username='regular', email='regular@example.com', is_admin=False)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()
    return user

class TestAdminToggleAdmin:
    def test_admin_toggle_admin_success(self, client, admin_user, regular_user, app):
        app.config['WTF_CSRF_ENABLED'] = False
        with client:
            client.post(f'/admin/users/{regular_user.id}/toggle-admin')
            assert current_app.extensions['sqlalchemy'].session.query(User).filter(User.id == regular_user.id).first().is_admin is True

    def test_flash_message_on_success(self, client, admin_user, regular_user, app):
        app.config['WTF_CSRF_ENABLED'] = False
        with client:
            response = client.post(f'/admin/users/{regular_user.id}/toggle-admin', follow_redirects=True)
            assert '管理者権限がトグルされました。'.encode('utf-8') in response.data

    def test_redirect_after_toggle(self, client, admin_user, regular_user, app):
        app.config['WTF_CSRF_ENABLED'] = False
        with client:
            response = client.post(f'/admin/users/{regular_user.id}/toggle-admin')
            assert response.status_code == 302
            assert response.location == '/admin/users'

    def test_logging_on_commit_failure(self, client, admin_user, regular_user, caplog, app, monkeypatch, db_session):
        app.config['WTF_CSRF_ENABLED'] = False

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)

        with client, caplog.at_level(logging.ERROR):
            client.post(f'/admin/users/{regular_user.id}/toggle-admin')
            assert 'Error toggling admin status' in caplog.text

    def test_flash_message_on_failure(self, client, admin_user, regular_user, app, monkeypatch, db_session):
        app.config['WTF_CSRF_ENABLED'] = False

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)
        with client:
            response = client.post(f'/admin/users/{regular_user.id}/toggle-admin', follow_redirects=True)
            assert '管理者権限のトグル中にエラーが発生しました'.encode('utf-8') in response.data

    def test_database_rollback_on_exception(self, client, admin_user, regular_user, app, monkeypatch, db_session):
        app.config['WTF_CSRF_ENABLED'] = False

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)
        with client:
            response = client.post(f'/admin/users/{regular_user.id}/toggle-admin', follow_redirects=True)
            assert app.extensions['sqlalchemy'].session.query(User).filter(User.id == regular_user.id).first().is_admin is False