from dotenv import load_dotenv
import os

# 環境変数を読み込む
load_dotenv()

# デバッグ用：環境変数の値を確認
print("DEBUG: Environment variables in wsgi.py:")
print(f"MYSQL_HOST: {os.environ.get('MYSQL_HOST')}")
print(f"MYSQL_DATABASE: {os.environ.get('MYSQL_DATABASE')}")
print(f"MYSQL_USER: {os.environ.get('MYSQL_USER')}")

from app import create_app, db

app = create_app() 