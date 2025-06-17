import pytest
from app import create_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy # This import is no longer needed here, but kept for clarity if Base is imported here
from models import User # Userモデルをインポート

@pytest.fixture
def app():
    # Create the Flask app instance with TESTING mode enabled
    flask_app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    # 例外がエラーハンドラーに伝播するように設定
    flask_app.config["PROPAGATE_EXCEPTIONS"] = False

    # Get the db instance that was initialized with the app
    test_db_instance = flask_app.extensions['sqlalchemy']

    with flask_app.app_context():
        # Create all tables on the in-memory database using the returned db_instance
        test_db_instance.create_all()

        yield flask_app # Yield the app for tests to run

        # Clean up: drop all tables from the in-memory test database
        test_db_instance.session.remove()
        test_db_instance.drop_all()

@pytest.fixture
def db_session(app):
    test_db = app.extensions['sqlalchemy'] # This will be our test_db_instance
    with app.app_context():
        yield test_db.session
        test_db.session.rollback()

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
def authenticated_user(app, db_session):
    with app.app_context():
        user = User(username='testuser', email='test@example.com', is_active=True)
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        # セッションにアタッチされた状態のユーザーを返す
        return db_session.query(User).filter_by(username='testuser').first()
