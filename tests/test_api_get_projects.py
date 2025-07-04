import pytest
from models import Order
from routes import main_bp
from datetime import date
import routes

@pytest.fixture
def client(app):
    return app.test_client()

class TestApiGetProjects:

    def test_api_get_projects_success(self, client, authenticated_user, db_session):
        order1 = Order(customer_name='Test Customer', project_name='Project A', order_date=date(2025, 6, 17))
        order2 = Order(customer_name='Test Customer', project_name='Project B', order_date=date(2025, 6, 17))
        db_session.add_all([order1, order2])
        db_session.commit()

        response = client.get('/api/projects')
        assert response.status_code == 200
        data = response.get_json()
        assert 'projects' in data
        assert set(data['projects']) == {'Project A', 'Project B'}

    def test_api_get_projects_rate_limit(self, client, authenticated_user):
        for _ in range(60):
            response = client.get('/api/projects')
            assert response.status_code == 200

        response = client.get('/api/projects')
        assert response.status_code == 429

    def test_api_get_projects_authentication_required(self, client):
        response = client.get('/api/projects')
        assert response.status_code == 401  # APIエンドポイントなので401を期待

    def test_api_get_projects_db_connection_failure(self, client, authenticated_user, monkeypatch, app):
        def mock_query_method(*args, **kwargs):
            raise Exception("Simulated database connection error")

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', mock_query_method)

        response = client.get('/api/projects')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    def test_api_get_projects_empty_list(self, client, authenticated_user):
        response = client.get('/api/projects')
        assert response.status_code == 200
        data = response.get_json()
        assert data['projects'] == []

    def test_api_get_projects_unexpected_exception(self, client, authenticated_user, monkeypatch, app):
        def mock_query_method(*args, **kwargs):
            raise Exception("Unexpected error")

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', mock_query_method)

        response = client.get('/api/projects')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data