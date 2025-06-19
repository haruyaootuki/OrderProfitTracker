import pytest
from models import User
import logging
from bs4 import BeautifulSoup

@pytest.fixture
def client(app):
    return app.test_client()

class TestDeleteUser:

    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the orders page."""
        response = client.get('/orders')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_delete_user_success(self, client, authenticated_user, db_session):
        user_to_delete = User(username='deleteuser', email='deleteuser@example.com', is_active=True)
        user_to_delete.set_password('deletepassword')
        db_session.add(user_to_delete)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        response = client.post(
            '/user/delete',
            json={'id': user_to_delete.id},
            headers=headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == 'ユーザーが削除されました'

    def test_delete_user_rate_limit(self, client, authenticated_user, db_session):
        user_to_delete = User(username='deleteuser', email='deleteuser@example.com', is_active=True)
        user_to_delete.set_password('deletepassword')
        db_session.add(user_to_delete)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        for _ in range(5):
            client.post('/user/delete', json={'id': user_to_delete.id}, headers=headers)

        response = client.post('/user/delete', json={'id': user_to_delete.id}, headers=headers)
        assert response.status_code == 429

    def test_delete_user_success_message(self, client, authenticated_user, db_session):
        user_to_delete = User(username='deleteuser', email='deleteuser@example.com', is_active=True)
        user_to_delete.set_password('deletepassword')
        db_session.add(user_to_delete)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        response = client.post(
            '/user/delete',
            json={'id': user_to_delete.id},
            headers=headers
        )
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == 'ユーザーが削除されました'

    def test_delete_user_no_id(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        response = client.post('/user/delete', json={}, headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'ユーザーIDが指定されていません'

    def test_delete_user_nonexistent_id(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        response = client.post('/user/delete', json={'id': 9999}, headers=headers)
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '指定されたユーザーが見つかりません'

    def test_delete_user_db_error(self, client, authenticated_user, db_session, monkeypatch):
        user_to_delete = User(username='deleteuser', email='deleteuser@example.com', is_active=True)
        user_to_delete.set_password('deletepassword')
        db_session.add(user_to_delete)
        db_session.commit()

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        response = client.post(
            '/user/delete',
            json={'id': user_to_delete.id},
            headers=headers
        )
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'ユーザー削除中にエラーが発生しました'