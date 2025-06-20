import os
import logging
import traceback
from flask import Flask, current_app, request, jsonify, flash, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# 環境変数を読み込む（開発環境用）
if not os.environ.get('VERCEL'):
    load_dotenv()

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """HTTPエラーのハンドリング"""
        # エラーをログに記録
        app.logger.error(f"HTTP error occurred: {error.code} - {error.name}")
        
        # APIリクエストの場合はJSONレスポンスを返す
        if request.path.startswith('/api/'):
            response = {
                'error': {
                    'code': error.code,
                    'name': error.name,
                    'description': error.description
                }
            }
            return jsonify(response), error.code
        
        # HTMLリクエストの場合はエラーページを返す
        try:
            # エラーコードに対応するテンプレートがある場合はそれを使用
            return render_template(f'{error.code}.html'), error.code
        except:
            # テンプレートがない場合は汎用エラーページを使用
            return render_template('error.html', error=error), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """予期しないエラーのハンドリング"""
        # エラーをログに記録
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        # APIリクエストの場合
        if request.path.startswith('/api/'):
            if app.debug:
                # デバッグモードの場合は詳細情報を含める
                response = {
                    'error': {
                        'code': 500,
                        'name': 'Internal Server Error',
                        'description': str(error),
                        'type': type(error).__name__,
                        'stack_trace': traceback.format_exc()
                    }
                }
            else:
                # 本番環境では詳細情報は含めない
                response = {
                    'error': {
                        'code': 500,
                        'name': 'Internal Server Error',
                        'description': '予期しないエラーが発生しました'
                    }
                }
            return jsonify(response), 500
        
        # HTMLリクエストの場合
        return render_template('500.html'), 500

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

    # エラーハンドラーを登録
    register_error_handlers(app)

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
        MYSQL_PORT = os.environ.get("MYSQL_PORT", "4000")

        if all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
            MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
            app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
        else:
            missing_vars = [var for var, value in {
                'MYSQL_USER': MYSQL_USER,
                'MYSQL_PASSWORD': MYSQL_PASSWORD,
                'MYSQL_HOST': MYSQL_HOST,
                'MYSQL_DATABASE': MYSQL_DATABASE
            }.items() if not value]
            error_msg = f"Missing required MySQL environment variables: {', '.join(missing_vars)}"
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
else:
    app = create_app()  # Vercelなどの本番環境用
