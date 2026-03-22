from flask import Flask
from app.config import Config
from app.db import close_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import main
    app.register_blueprint(main)

    app.teardown_appcontext(close_db)
    return app
