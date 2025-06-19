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
# from dotenv import load_dotenv # この行を削除またはコメントアウト

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# load_dotenv()に関する以下の行を削除またはコメントアウト
# if not os.getenv('VERCEL_ENV'):
#     load_dotenv()

class Base(DeclarativeBase):
    pass

# REMOVE GLOBAL db instance. It will be created inside create_app.
# db = SQLAlchemy(model_class=Base)

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address
)

def create_app(test_config=None):
    # Create Flask app
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Apply test config if provided
    if test_config is None:
        app.config["TESTING"] = False # Default to False
    else:
        app.config.update(test_config)

    # Database configuration
    if app.config["TESTING"]:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    
    # デバッグ用: DATABASE_URLの値をログに出力
    print(f"DEBUG: DATABASE_URL from os.environ: {os.environ.get('DATABASE_URL')}")
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI in app.config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # Create db instance for THIS app instance AFTER config is set
    db_instance = SQLAlchemy(model_class=Base)

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}") # デバッグ用に追加

    # Security configurations
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600 # 1時間 (3600秒) に設定
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize extensions with app
    db_instance.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Login manager configuration
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
        # dbインスタンスはcurrent_app.extensions['sqlalchemy']から取得
        db_from_current_app = current_app.extensions['sqlalchemy']
        from models import User
        return db_from_current_app.session.query(User).get(int(user_id))
    
    # Register blueprints here
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    return app

# Create the app instance
# app = create_app() # This line should remain commented out for testing
# Import routes after the app is created to avoid circular imports
# import routes

# Vercelデプロイ用にアプリケーションインスタンスを作成
# if os.getenv('VERCEL_ENV'): # この行を削除またはコメントアウト
#     app = create_app() # この行を削除またはコメントアウト

# アプリケーションインスタンスを無条件で作成
app = create_app()
