import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# Vercel環境かどうかを確認
IS_VERCEL = os.environ.get('VERCEL', False)
print(f"Running on Vercel: {IS_VERCEL}")

# 現在の環境変数をすべて表示（パスワードは除く）
print("\nAll environment variables:")
for key, value in os.environ.items():
    if 'PASSWORD' not in key.upper():
        print(f"{key}: {value}")

# データベース接続情報を明示的に設定（Vercel環境用）
if IS_VERCEL:
    print("\nSetting database connection for Vercel environment")
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

from app import create_app, db

app = create_app() 