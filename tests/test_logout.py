import pytest
from flask_login import current_user
from models import User
from bs4 import BeautifulSoup

class TestLogout:

    def test_user_successful_logout(self, client, db_session, authenticated_user):
        # authenticated_userフィクスチャがユーザーをログイン済み状態にするため、追加のログインは不要
        # self._login_user_for_test(client, authenticated_user)

        # Now attempt to logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        assert 'ログアウトしました' in soup.find('div', class_='alert').text
        assert '/login' in response.request.path

    def test_redirect_to_login_after_logout(self, client, db_session, authenticated_user):
        # authenticated_userフィクスチャがユーザーをログイン済み状態にするため、追加のログインは不要
        # self._login_user_for_test(client, authenticated_user)

        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200 # After redirect to login page
        assert '/login' in response.request.path

    def test_logout_fails_when_not_logged_in(self, client):
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']