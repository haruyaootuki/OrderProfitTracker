import pytest
from flask import url_for
from flask_login import current_user
from routes import main_bp
from models import User

@pytest.fixture
def client(app):
    return app.test_client()

class TestProfitAnalysisPage:

    def test_render_profit_analysis_authenticated(self, client, authenticated_user):
        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 200
        assert '利益分析'.encode('utf-8') in response.data

    def test_redirect_unauthenticated_to_login(self, client):
        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 302
        assert url_for('main.login') in response.headers['Location']

    def test_display_profit_analysis_template(self, client, authenticated_user):
        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 200
        assert '利益分析'.encode('utf-8') in response.data

    def test_missing_profit_analysis_template(self, client, authenticated_user, monkeypatch, app):
        original_render_template = app.jinja_env.get_template

        def mock_render_template(template_name, *args, **kwargs):
            if template_name == 'profit_analysis.html':
                raise Exception("Template not found")
            return original_render_template(template_name, *args, **kwargs)

        monkeypatch.setattr(app.jinja_env, 'get_template', mock_render_template)

        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 500

    def test_access_with_invalid_session(self, client, db_session):
        user = User(username='invaliduser', email='invaliduser@example.com', is_active=True)
        user.set_password('password')
        db_session.add(user)
        db_session.commit()

        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 302
        assert url_for('main.login') in response.headers['Location']

    def test_login_required_decorator(self, client):
        response = client.get(url_for('main.profit_analysis'))
        assert response.status_code == 302
        assert url_for('main.login') in response.headers['Location']