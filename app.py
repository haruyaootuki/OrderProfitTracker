import os
import logging
from flask import Flask, current_app, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# グローバルなlimiterインスタンスは保持（init_appでアプリケーションにアタッチ）
limiter = Limiter(
    key_func=get_remote_address
)

# グローバルなlogin_managerとcsrfインスタンス
login_manager = LoginManager()
csrf = CSRFProtect()

# グローバルスコープでappを宣言（初期値はNone）
app = None

def create_app(test_config=None):
    global app # グローバル変数を参照
    # Flaskアプリケーションの作成
    app = Flask(__name__)
    
    # 設定
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # テスト設定が提供されている場合は適用
    if test_config is None:
        app.config["TESTING"] = False # デフォルトはFalse
    else:
        app.config.update(test_config)

    # データベース設定
    if app.config["TESTING"]:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        # SQLAlchemy エンジンオプションを先に設定
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
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
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # 環境変数の取得とバリデーション
        MYSQL_USER = os.environ.get("MYSQL_USER")
        MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
        MYSQL_HOST = os.environ.get("MYSQL_HOST")
        MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
        MYSQL_PORT = os.environ.get("MYSQL_PORT", "4000")  # デフォルトポートを4000に設定

        print("\nVercel Environment:", "Yes" if os.environ.get('VERCEL') else "No")
        print("\nDatabase Configuration:")
        print(f"Host: {MYSQL_HOST}")
        print(f"Port: {MYSQL_PORT}")
        print(f"Database: {MYSQL_DATABASE}")
        print(f"User: {MYSQL_USER}")

        if all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
            # TiDB Cloud用の接続文字列を構築
            MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
            app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
            
            print("\nDatabase connection configured successfully")
            print(f"Connection string (without password): mysql+pymysql://{MYSQL_USER}:****@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        else:
            missing_vars = [var for var, value in {
                'MYSQL_USER': MYSQL_USER,
                'MYSQL_PASSWORD': MYSQL_PASSWORD,
                'MYSQL_HOST': MYSQL_HOST,
                'MYSQL_DATABASE': MYSQL_DATABASE
            }.items() if not value]
            error_msg = f"Missing required MySQL environment variables: {', '.join(missing_vars)}"
            print(f"\nConfiguration Error: {error_msg}")
            raise ValueError(error_msg)

    # このアプリインスタンス用のdbインスタンスを、設定が完了した後に作成
    db.init_app(app)

    # セキュリティ設定
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600 # 1時間 (3600秒) に設定
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 拡張機能をアプリで初期化
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app) # limiterもここで初期化
    
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
    
    # ブループリントを登録
    from routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        import models  # noqa: F401

        if app.config["TESTING"]:
            db.create_all()
    
    return app # アプリを返す

# アプリケーションが直接実行された場合にのみインスタンスを作成
if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
