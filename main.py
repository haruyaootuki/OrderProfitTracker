from app import create_app
import routes  # noqa: F401

if __name__ == "__main__":
    app, db = create_app() # create_app()を呼び出してappとdbインスタンスを取得
    app.run(host="0.0.0.0", port=5000, debug=True)
