import pytest
from flask import url_for
from flask_login import current_user, login_user
from models import User
from bs4 import BeautifulSoup

class TestLogout:

    def _login_user_for_test(self, client, user):
        """Helper to log in a user for tests, handling CSRF."""
        # Get CSRF token
        response = client.get(url_for('main.login'))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

        login_response = client.post(
            url_for('main.login'),
            data={
                'username': user.username,
                'password': 'password', # Assuming default password from authenticated_user fixture
                'csrf_token': csrf_token
            },
            follow_redirects=True
        )
        assert login_response.status_code == 200
        assert 'ログインしました'.encode('utf-8') in login_response.data
        return login_response

    def test_user_successful_logout(self, client, db_session, authenticated_user):
        # Log in the user
        self._login_user_for_test(client, authenticated_user)

        # Now attempt to logout
        response = client.get(url_for('main.logout'), follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        assert 'ログアウトしました' in soup.find('div', class_='alert').text
        assert url_for('main.login') in response.request.path

    def test_redirect_to_login_after_logout(self, client, db_session, authenticated_user):
        self._login_user_for_test(client, authenticated_user)

        response = client.get(url_for('main.logout'), follow_redirects=True)
        assert response.status_code == 200 # After redirect to login page
        assert url_for('main.login') in response.request.path

    def test_logout_fails_when_not_logged_in(self, client):
        response = client.get(url_for('main.logout'))
        assert response.status_code == 302
        assert url_for('main.login') in response.headers['Location']