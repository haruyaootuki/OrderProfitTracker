from dotenv import load_dotenv

load_dotenv()

import os
import logging
from flask import Flask, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# グローバルなインスタンス
limiter = Limiter(key_func=get_remote_address)
login_manager = LoginManager()
csrf = CSRFProtect()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# MySQL database configuration
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "4000")

if all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
    # Configure MySQL database URI
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
else:
    # 開発環境用のフォールバックURI
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    print("Warning: Using in-memory SQLite database as fallback")

# SQLAlchemy engine options
engine_options = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 2,
    "connect_args": {
        "connect_timeout": 10,
        "ssl": {
            "verify_identity": True
        } if os.environ.get('VERCEL') else {}
    }
}

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# セキュリティ設定
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 拡張機能の初期化
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
limiter.init_app(app)

# ログインマネージャー設定
login_manager.login_view = 'main.login'
login_manager.login_message = 'ログインが必要です。'
login_manager.login_message_category = 'info'

@login_manager.unauthorized_handler
def unauthorized():
    # APIエンドポイントの場合、401 Unauthorizedを返す
    if request.blueprint == 'main' and request.path.startswith('/api/'):
        return jsonify({'error': '認証が必要です'}), 401
    # それ以外の場合はログインページにリダイレクト
    flash('ログインが必要です。アクセスするにはログインしてください。', 'info')
    return redirect(url_for('main.login'))

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.query(User).get(int(user_id))

with app.app_context():
    # 環境変数が設定されていない場合のエラー処理
    if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]) and os.environ.get('VERCEL'):
        missing_vars = [var for var, value in {
            'MYSQL_USER': MYSQL_USER,
            'MYSQL_PASSWORD': MYSQL_PASSWORD,
            'MYSQL_HOST': MYSQL_HOST,
            'MYSQL_DATABASE': MYSQL_DATABASE
        }.items() if not value]
        error_msg = f"Missing required MySQL environment variables: {', '.join(missing_vars)}"
        raise ValueError(error_msg)

    import models  # noqa: F401
    db.create_all()

# ブループリントを登録
from routes import main_bp
app.register_blueprint(main_bp)

# アプリケーションが直接実行された場合にのみデバッグモードを有効化
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
