import pytest
from flask import url_for
import logging
from datetime import date
from models import Order, User
from bs4 import BeautifulSoup


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_user(client, db_session):
    user = User(username='testuser', email='testuser@example.com', is_active=True)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()

    response = client.get(url_for('main.login'))
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

    client.post(
        url_for('main.login'),
        data={
            'username': user.username,
            'password': 'password',
            'csrf_token': csrf_token
        },
        follow_redirects=True
    )
    return user

class TestApiDeleteOrder:

    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the orders page."""
        response = client.get(url_for('main.orders'))
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_successful_order_deletion(self, client, authenticated_user, db_session):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.delete(
            url_for('main.api_delete_order', order_id=order.id),
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == '受注が削除されました'

    def test_order_deletion_logging(self, client, authenticated_user, db_session, caplog):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        with caplog.at_level(logging.INFO):
            client.delete(
                url_for('main.api_delete_order', order_id=order.id),
                headers={'X-CSRFToken': csrf_token}
            )
            assert any('Order deleted for project: Old Project' in message for message in caplog.messages)

    def test_order_deletion_success_message(self, client, authenticated_user, db_session):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.delete(
            url_for('main.api_delete_order', order_id=order.id),
            headers={'X-CSRFToken': csrf_token}
        )
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == '受注が削除されました'

    def test_delete_non_existent_order(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.delete(
            url_for('main.api_delete_order', order_id=9999),
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 404

    def test_order_deletion_without_authentication(self, client, db_session, monkeypatch, app):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        # テスト実行中のみCSRF保護を一時的に無効にする
        monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', False)

        response = client.delete(url_for('main.api_delete_order', order_id=order.id))
        assert response.status_code == 401

    def test_order_deletion_database_error(self, client, authenticated_user, db_session, monkeypatch):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(db_session, 'commit', mock_commit)

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.delete(
            url_for('main.api_delete_order', order_id=order.id),
            headers={'X-CSRFToken': csrf_token}
        )
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '受注削除中にエラーが発生しました'