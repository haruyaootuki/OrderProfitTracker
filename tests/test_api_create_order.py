import pytest
from models import Order, User
from routes import main_bp
from datetime import date
import routes
from bs4 import BeautifulSoup
import logging


@pytest.fixture
def client(app):
    return app.test_client()

class TestApiCreateOrder:

    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the orders page."""
        response = client.get('/orders')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def test_create_order_success(self, client, authenticated_user, db_session):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None # Ensure token is retrieved
        response = client.post(
            '/api/orders',
            data={
                'customer_name': 'Test Customer',
                'project_name': 'Test Project',
                'sales_amount': '1000',  # Convert to string
                'order_amount': '1000',  # Convert to string
                'invoiced_amount': '500',  # Convert to string
                'order_date': str(date.today()), # Convert date to string 'YYYY-MM-DD'
                'contract_type': 'Type A',
                'sales_stage': 'Stage 1',
                'billing_month': str(date.today()),
                'work_in_progress': 'y',  # Convert boolean to string ('y' for True)
                'description': 'Test order',
                'csrf_token': csrf_token # Add CSRF token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == '受注が登録されました'

    def test_order_creation_rate_limit(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        # Prepare data with CSRF token and string values
        data = {
            'customer_name': 'Rate Limit Test',
            'project_name': 'Rate Limit Project',
            'sales_amount': '100',
            'order_amount': '100',
            'invoiced_amount': '50',
            'order_date': str(date.today()),
            'contract_type': 'Type B',
            'sales_stage': 'Stage 2',
            'billing_month': str(date.today()),
            'work_in_progress': 'n', # Convert boolean to string ('n' for False)
            'description': 'Rate limit test order',
            'csrf_token': csrf_token
        }
        for _ in range(30):
            response = client.post('/api/orders', data=data, content_type='application/x-www-form-urlencoded')
            assert response.status_code == 201 # Now that CSRF is handled, these should be 201
        response = client.post('/api/orders', data=data, content_type='application/x-www-form-urlencoded') # Last request should hit rate limit
        assert response.status_code == 429

    def test_order_creation_logging_success(self, client, authenticated_user, caplog):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        with caplog.at_level(logging.INFO):
            client.post(
                '/api/orders',
                data={
                    'customer_name': 'Test Customer',
                    'project_name': 'Test Project',
                    'sales_amount': '1000',
                    'order_amount': '1000',
                    'invoiced_amount': '500',
                    'order_date': str(date.today()),
                    'contract_type': 'Type A',
                    'sales_stage': 'Stage 1',
                    'billing_month': str(date.today()),
                    'work_in_progress': 'y',
                    'description': 'Test order',
                    'csrf_token': csrf_token
                },
                content_type='application/x-www-form-urlencoded'
            )
            # caplog.records をループしてメッセージを確認する
            found_log_message = False
            for record in caplog.records:
                if "Order created for project: Test Project" in record.message:
                    found_log_message = True
                    break
            assert found_log_message

    def test_create_order_invalid_data(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        # Send minimal data with CSRF to trigger validation failure on required fields
        # 'customer_name' and 'project_name' are DataRequired
        response = client.post('/api/orders', data={'csrf_token': csrf_token}, content_type='application/x-www-form-urlencoded') # Send minimal data with CSRF to trigger validation
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'バリデーションエラー'
        assert 'errors' in data # Check for the 'errors' key
        assert 'customer_name' in data['errors'] # Example check for a specific error
        assert 'project_name' in data['errors']
        assert 'order_date' in data['errors']

    def test_create_order_database_error(self, client, authenticated_user, monkeypatch):
        def mock_commit():
            raise Exception("Simulated database error")

        monkeypatch.setattr(routes.current_app.extensions['sqlalchemy'].session, 'commit', mock_commit)

        csrf_token = self._get_csrf_token(client)
        assert csrf_token is not None
        response = client.post(
            '/api/orders',
            data={
                'customer_name': 'Test Customer',
                'project_name': 'Test Project',
                'sales_amount': '1000',
                'order_amount': '1000',
                'invoiced_amount': '500',
                'order_date': str(date.today()),
                'contract_type': 'Type A',
                'sales_stage': 'Stage 1',
                'billing_month': str(date.today()),
                'work_in_progress': 'y',
                'description': 'Test order',
                'csrf_token': csrf_token
            },
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '受注登録中にエラーが発生しました'

    def test_create_order_unauthenticated(self, client, monkeypatch, app):
        # テスト実行中のみCSRF保護を一時的に無効にする
        monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', False)

        # When unauthenticated, Flask-Login's @login_required decorator should redirect to login
        # For API endpoints, it usually returns 401 Unauthorized if not redirected.
        # Since it's an API, we expect 401.
        # No CSRF token is needed here as the request should be blocked before CSRF validation.
        response = client.post('/api/orders', data={}, content_type='application/x-www-form-urlencoded') # Data can be empty if it's blocked by login_required
        assert response.status_code == 401