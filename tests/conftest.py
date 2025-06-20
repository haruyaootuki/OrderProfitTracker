import os
import pytest
from app import create_app, limiter, db # dbをインポート
from flask_login import UserMixin
# from flask_sqlalchemy import SQLAlchemy # この行はもう不要です
from models import User # Userモデルをインポート
from bs4 import BeautifulSoup # BeautifulSoupをインポート

# Flask-Limiterのデコレータをテスト中に無効にするためのモックデコレータは不要になりました
# def no_op_limit_decorator(*args, **kwargs):
#     def decorator(f):
#         return f
#     return decorator

# @pytest.fixture(autouse=True)
# def disable_rate_limits(monkeypatch):
#     monkeypatch.setattr(limiter, 'limit', no_op_limit_decorator)

# テスト環境であることを明示
os.environ['TESTING'] = 'true'

@pytest.fixture
def app():
    # Flask appインスタンスをcreate_appで作成し、TESTINGモードを有効にする
    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,  # テスト時はCSRFチェックを無効化
        "SESSION_COOKIE_SECURE": False  # テスト時はセキュアクッキーを無効化
    })
    
    # 例外がエラーハンドラーに伝播するように設定
    flask_app.config["PROPAGATE_EXCEPTIONS"] = False

    with flask_app.app_context():
        # インメモリデータベースにすべてのテーブルを作成
        db.create_all()
        yield flask_app
        # クリーンアップ: インメモリテストデータベースからすべてのテーブルを削除
        db.session.remove()
        db.drop_all()

@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()

class TestUser(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)

@pytest.fixture
def test_user():
    return TestUser(id=1)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def authenticated_user(app, client, db_session):
    user = User(username='testuser', email='test@example.com', is_active=True)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()

    # ログインページからCSRFトークンを取得
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

    # CSRFトークンを含めてログイン
    client.post(
        '/login',
        data={
            'username': user.username,
            'password': 'password',
            'csrf_token': csrf_token
        },
        follow_redirects=True
    )
    # セッションにアタッチされた状態のユーザーを返す
    return db_session.query(User).filter_by(username='testuser').first()

@pytest.fixture
def admin_user(app, client, db_session):
    # 管理者ユーザー作成
    user = User(username='admin', email='admin@example.com', is_admin=True, is_active=True)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()

    # ログインページからCSRFトークンを取得
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

    # CSRFトークンを含めてログイン
    client.post(
        '/login',
        data={
            'username': user.username,
            'password': 'password',
            'csrf_token': csrf_token
        },
        follow_redirects=True
    )
    # セッションにアタッチされた状態のユーザーを返す
    return db_session.query(User).filter_by(username='admin').first()
