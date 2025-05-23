from flask import Flask
from flask_migrate import Migrate

from app.config import DevelopmentConfig
from app.db import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate = Migrate(app, db)

    from app.routes.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    return app
