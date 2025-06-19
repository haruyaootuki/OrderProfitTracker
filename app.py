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

# VERCEL_ENVのチェックを削除し、常に.envファイルを読み込む
load_dotenv()

class Base(DeclarativeBase):
    pass

# グローバルなlimiterインスタンスは保持（init_appでアプリケーションにアタッチ）
limiter = Limiter(
    key_func=get_remote_address
)

# グローバルなlogin_managerとcsrfインスタンス
login_manager = LoginManager()
csrf = CSRFProtect()

# グローバルスコープでappとdbを宣言（初期値はNone）
app = None
db = None

def create_app(test_config=None):
    global app, db # グローバル変数を参照
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
        # 個別のMySQL環境変数からURIを構築
        MYSQL_USER = os.environ.get("MYSQL_USER")
        MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
        MYSQL_HOST = os.environ.get("MYSQL_HOST")
        MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")

        # MySQLデータベースURIを設定
        MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"

        # DATABASE_URLが存在しない場合、MYSQL_URIをフォールバックとして使用
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", MYSQL_URI)
    
    # デバッグ用: DATABASE_URLの値をログに出力
    print(f"DEBUG: DATABASE_URL from os.environ: {os.environ.get('DATABASE_URL')}")
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI in app.config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # このアプリインスタンス用のdbインスタンスを、設定が完了した後に作成
    db_instance = SQLAlchemy(model_class=Base)

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # セキュリティ設定
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600 # 1時間 (3600秒) に設定
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 拡張機能をアプリで初期化
    db_instance.init_app(app)
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
        # dbインスタンスはcurrent_app.extensions['sqlalchemy']から取得
        db_from_current_app = current_app.extensions['sqlalchemy']
        from models import User
        return db_from_current_app.session.query(User).get(int(user_id))
    
    # ブループリントを登録
    from routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # ここでモデルをインポートしないとテーブルが作成されません
        import models  # noqa: F401
        db_instance.create_all()
    
    return app, db_instance # アプリとdbインスタンスを返す

# 循環インポートを防ぐため、アプリが作成された後にルートをインポート
# import routes # noqa: F401

app, db = create_app()
