import pytest
from flask import url_for
from models import Order, User
from routes import main_bp
from datetime import date
import routes
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

class TestApiGetProjects:

    def test_api_get_projects_success(self, client, authenticated_user, db_session):
        order1 = Order(customer_name='Test Customer', project_name='Project A', order_date=date(2025, 6, 17))
        order2 = Order(customer_name='Test Customer', project_name='Project B', order_date=date(2025, 6, 17))
        db_session.add_all([order1, order2])
        db_session.commit()

        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 200
        data = response.get_json()
        assert 'projects' in data
        assert set(data['projects']) == {'Project A', 'Project B'}

    def test_api_get_projects_rate_limit(self, client, authenticated_user):
        for _ in range(60):
            response = client.get(url_for('main.api_get_projects'))
            assert response.status_code == 200

        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 429

    def test_api_get_projects_authentication_required(self, client):
        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 401  # APIエンドポイントなので401を期待

    def test_api_get_projects_db_connection_failure(self, client, authenticated_user, monkeypatch, app):
        def mock_query_method(*args, **kwargs):
            raise Exception("Simulated database connection error")

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', mock_query_method)

        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    def test_api_get_projects_empty_list(self, client, authenticated_user):
        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 200
        data = response.get_json()
        assert data['projects'] == []

    def test_api_get_projects_unexpected_exception(self, client, authenticated_user, monkeypatch, app):
        def mock_query_method(*args, **kwargs):
            raise Exception("Unexpected error")

        monkeypatch.setattr(app.extensions['sqlalchemy'].session, 'query', mock_query_method)

        response = client.get(url_for('main.api_get_projects'))
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data