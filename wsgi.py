from app import create_app

app, db = create_app(skip_create_all=True) 