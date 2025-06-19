import pytest
from datetime import datetime, date
from models import User, Order
from bs4 import BeautifulSoup

class TestApiGetProfitData:
    def _get_csrf_token(self, client):
        """Helper to get CSRF token from the login page."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            return csrf_token.get('value')
        return None

    def _create_dummy_order(self, db_session, customer_name, project_name, sales_amount, order_amount, invoiced_amount, order_date, contract_type, sales_stage, billing_month, work_in_progress, description):
        order = Order(
            customer_name=customer_name,
            project_name=project_name,
            sales_amount=sales_amount,
            order_amount=order_amount,
            invoiced_amount=invoiced_amount,
            order_date=order_date,
            contract_type=contract_type,
            sales_stage=sales_stage,
            billing_month=billing_month,
            work_in_progress=work_in_progress,
            description=description
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_api_get_profit_data_specific_project(self, client, authenticated_user, db_session):
        self._create_dummy_order(db_session, 'Customer A', 'ProjectX', 1000, 900, 800, date(2023, 1, 5), 'Type1', 'Stage1', date(2023, 1, 31), True, 'Desc1')
        self._create_dummy_order(db_session, 'Customer B', 'ProjectX', 2000, 1800, 1600, date(2023, 1, 10), 'Type2', 'Stage2', date(2023, 1, 31), False, 'Desc2')
        self._create_dummy_order(db_session, 'Customer C', 'ProjectY', 5000, 4500, 4000, date(2023, 1, 15), 'Type3', 'Stage3', date(2023, 1, 31), True, 'Desc3')

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}
        response = client.get('/api/profit-data?project_name=ProjectX&start_date=2023-01-01&end_date=2023-01-31', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        
        expected_sales = 1000 + 2000
        expected_order = 900 + 1800
        expected_invoiced = 800 + 1600

        assert data['total_sales_amount'] == expected_sales
        assert data['total_order_amount'] == expected_order
        assert data['total_invoiced_amount'] == expected_invoiced

    def test_api_get_profit_data_all_projects(self, client, authenticated_user, db_session):
        self._create_dummy_order(db_session, 'Customer D', 'ProjectA', 100, 90, 80, date(2023, 1, 1), 'TypeX', 'StageX', date(2023, 1, 31), True, 'DescX')
        self._create_dummy_order(db_session, 'Customer E', 'ProjectB', 200, 180, 160, date(2023, 1, 2), 'TypeY', 'StageY', date(2023, 1, 31), False, 'DescY')

        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}
        response = client.get('/api/profit-data?project_name=all&start_date=2023-01-01&end_date=2023-01-31', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        
        expected_sales = 100 + 200
        expected_order = 90 + 180
        expected_invoiced = 80 + 160

        assert data['total_sales_amount'] == expected_sales
        assert data['total_order_amount'] == expected_order
        assert data['total_invoiced_amount'] == expected_invoiced

    def test_api_get_profit_data_rate_limiting(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}
        for _ in range(61):
            response = client.get('/api/profit-data?project_name=all&start_date=2023-01-01&end_date=2023-01-31', headers=headers)
        assert response.status_code == 429

    def test_api_get_profit_data_invalid_date_format(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}
        response = client.get('/api/profit-data?project_name=all&start_date=2023-01-01&end_date=invalid-date', headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '日付の形式が正しくありません。YYYY-MM-DD形式を使用してください。'

    def test_api_get_profit_data_missing_project_name(self, client, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}
        response = client.get('/api/profit-data?start_date=2023-01-01&end_date=2023-01-31', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_sales_amount' in data
        assert 'total_order_amount' in data
        assert 'total_invoiced_amount' in data

    def test_api_get_profit_data_database_error(self, client, monkeypatch, authenticated_user):
        csrf_token = self._get_csrf_token(client)
        headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

        def mock_query(*args, **kwargs):
            raise Exception("Database error")

        db_instance = client.application.extensions['sqlalchemy']
        monkeypatch.setattr(db_instance.session, 'query', mock_query)
        response = client.get('/api/profit-data?project_name=all&start_date=2023-01-01&end_date=2023-01-31', headers=headers)
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '利益データの計算中にエラーが発生しました'
