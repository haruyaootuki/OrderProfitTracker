import pytest
from flask import url_for
from models import Order, User
from bs4 import BeautifulSoup
from routes import main_bp
from datetime import date # datetime.dateをインポート
import routes # routesモジュールをインポート

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

class TestApiGetOrders:

    def test_api_get_orders_default_pagination(self, client, authenticated_user):
        response = client.get(url_for('main.api_get_orders'))
        assert response.status_code == 200
        data = response.get_json()
        assert 'orders' in data
        assert 'total' in data
        assert data['page'] == 1
        assert data['per_page'] == 50

    def test_api_get_orders_with_search(self, client, authenticated_user, db_session):
        order = Order(customer_name='Test Customer', project_name='Test Project', order_date=date(2025, 6, 17)) # dateオブジェクトに修正
        db_session.add(order)
        db_session.commit()

        response = client.get(url_for('main.api_get_orders', search='Test'))
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['orders']) > 0
        assert any('Test Customer' in order['customer_name'] for order in data['orders'])

    def test_api_get_orders_with_pagination_params(self, client, authenticated_user):
        response = client.get(url_for('main.api_get_orders', page=2, per_page=10))
        assert response.status_code == 200
        data = response.get_json()
        assert data['page'] == 2
        assert data['per_page'] == 10

    def test_api_get_orders_invalid_pagination_params(self, client, authenticated_user):
        response = client.get(url_for('main.api_get_orders', page='invalid', per_page='invalid'))
        assert response.status_code == 200
        data = response.get_json()
        assert data['page'] == 1
        assert data['per_page'] == 50

    def test_api_get_orders_no_matching_search(self, client, authenticated_user):
        response = client.get(url_for('main.api_get_orders', search='NonExistent'))
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['orders']) == 0

    def test_api_get_orders_server_error(self, client, authenticated_user, monkeypatch, app):
        # current_app.extensions['sqlalchemy'].session.query をモックして例外を発生させる
        def mock_query_method(*args, **kwargs):
            raise Exception("Simulated database query error")

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', mock_query_method)

        response = client.get(url_for('main.api_get_orders'))
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
