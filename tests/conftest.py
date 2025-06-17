import pytest
from app import app as flask_app, db # あなたのFlaskアプリケーションのインポートパスに合わせてください
from flask_login import UserMixin

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    flask_app.config.update({"TESTING": True})
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

class TestUser(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)


@pytest.fixture
def test_user():
    return TestUser(id=1) 
