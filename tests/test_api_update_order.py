import pytest
from models import Order, User
from routes import main_bp
from datetime import date
from bs4 import BeautifulSoup
import logging
import routes

@pytest.fixture
def client(app):
    return app.test_client()

class TestApiUpdateOrder:

    def _get_csrf_token(self, client):
        response = client.get('/orders')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_successful_order_update(self, client, authenticated_user, db_session):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.put(
            f'/api/orders/{order.id}',
            data={
                'customer_name': 'New Customer',
                'project_name': 'New Project',
                'sales_amount': '2000',
                'order_amount': '2000',
                'invoiced_amount': '1000',
                'order_date': str(date.today()),
                'contract_type': 'Type B',
                'sales_stage': 'Stage 2',
                'billing_month': str(date.today()),
                'work_in_progress': 'n',
                'description': 'Updated order',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == '受注が更新されました'

    def test_rate_limiting_allows_requests(self, client, authenticated_user, db_session, app):
        order = Order(customer_name='Rate Limit Customer', project_name='Rate Limit Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        data = {
            'customer_name': 'Rate Limit Customer',
            'project_name': 'Rate Limit Project',
            'sales_amount': '100',
            'order_amount': '100',
            'invoiced_amount': '50',
            'order_date': str(date.today()),
            'contract_type': 'Type B',
            'sales_stage': 'Stage 2',
            'billing_month': str(date.today()),
            'work_in_progress': 'n',
            'description': 'Rate limit test order',
            'csrf_token': csrf_token
        }
        for _ in range(30):
            response = client.put(f'/api/orders/{order.id}', data=data, content_type='application/x-www-form-urlencoded')
            assert response.status_code == 200
        response = client.put(f'/api/orders/{order.id}', data=data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 429

    def test_order_update_json_response(self, client, authenticated_user, db_session):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.put(
            f'/api/orders/{order.id}',
            data={
                'customer_name': 'New Customer',
                'project_name': 'New Project',
                'sales_amount': '2000',
                'order_amount': '2000',
                'invoiced_amount': '1000',
                'order_date': str(date.today()),
                'contract_type': 'Type B',
                'sales_stage': 'Stage 2',
                'billing_month': str(date.today()),
                'work_in_progress': 'n',
                'description': 'Updated order',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'order' in data
        assert data['order']['customer_name'] == 'New Customer'
        assert data['order']['project_name'] == 'New Project'

    def test_order_update_with_invalid_data(self, client, authenticated_user, db_session):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.put(
            f'/api/orders/{order.id}',
            data={'csrf_token': csrf_token},
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'バリデーションエラー'
        assert 'errors' in data

    def test_database_rollback_on_failure(self, client, authenticated_user, db_session, monkeypatch):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(routes.current_app.extensions['sqlalchemy'].session, 'commit', mock_commit)

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None

        response = client.put(
            f'/api/orders/{order.id}',
            data={
                'customer_name': 'New Customer',
                'project_name': 'New Project',
                'sales_amount': '2000',
                'order_amount': '2000',
                'invoiced_amount': '1000',
                'order_date': str(date.today()),
                'contract_type': 'Type B',
                'sales_stage': 'Stage 2',
                'billing_month': str(date.today()),
                'work_in_progress': 'n',
                'description': 'Updated order',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '受注更新中にエラーが発生しました'

    def test_unauthorized_user_cannot_update_order(self, client, db_session, monkeypatch, app):
        order = Order(customer_name='Old Customer', project_name='Old Project', order_date=date.today())
        db_session.add(order)
        db_session.commit()

        monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', False)

        response = client.put(
            f'/api/orders/{order.id}',
            data={},
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 401