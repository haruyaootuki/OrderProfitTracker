import os
from dotenv import load_dotenv

# 環境変数を読み込む（開発環境用）
if not os.environ.get('VERCEL'):
    load_dotenv()

# Vercel環境の確認
IS_VERCEL = bool(os.environ.get('VERCEL'))
print(f"Running on Vercel: {IS_VERCEL}")

# 現在の環境変数をすべて表示（パスワードは除く）
print("\nAll environment variables:")
env_vars = dict(os.environ)
for key in sorted(env_vars.keys()):
    if 'PASSWORD' not in key.upper() and 'SECRET' not in key.upper():
        print(f"{key}: {env_vars[key]}")

# データベース接続情報を確認
print("\nDatabase connection variables:")
db_vars = {
    'MYSQL_HOST': os.environ.get('MYSQL_HOST'),
    'MYSQL_PORT': os.environ.get('MYSQL_PORT', '4000'),
    'MYSQL_DATABASE': os.environ.get('MYSQL_DATABASE'),
    'MYSQL_USER': os.environ.get('MYSQL_USER')
}
print("Database variables present:")
for key, value in db_vars.items():
    print(f"{key}: {'[SET]' if value else '[NOT SET]'}")

from app import create_app, db

app = create_app() 