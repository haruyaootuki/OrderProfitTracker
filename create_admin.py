from app import app, db
from models import User
import getpass

def create_admin_account():
    with app.app_context():
        print("管理者アカウント作成ツール")
        print("------------------------")
        
        # ユーザー名の入力
        while True:
            username = input("管理者ユーザー名を入力してください: ").strip()
            if username:
                # 既存のユーザー名チェック
                if User.query.filter_by(username=username).first():
                    print("このユーザー名は既に使用されています。")
                    continue
                break
            print("ユーザー名を入力してください。")
        
        # メールアドレスの入力
        while True:
            email = input("メールアドレスを入力してください: ").strip()
            if email:
                if User.query.filter_by(email=email).first():
                    print("このメールアドレスは既に使用されています。")
                    continue
                break
            print("メールアドレスを入力してください。")
        
        # パスワードの入力
        while True:
            password = getpass.getpass("パスワードを入力してください: ").strip()
            if len(password) < 8:
                print("パスワードは8文字以上必要です。")
                continue
            
            confirm_password = getpass.getpass("パスワードを再入力してください: ").strip()
            if password != confirm_password:
                print("パスワードが一致しません。")
                continue
            break
        
        try:
            # 管理者アカウントの作成
            admin = User(username=username, email=email, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"\n管理者アカウント '{username}' が正常に作成されました。")
            return True
        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    create_admin_account() 