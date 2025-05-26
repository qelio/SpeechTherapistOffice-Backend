from flask_jwt_extended import JWTManager
from flask import Flask
from flask_migrate import Migrate
from datetime import timedelta
from flask_cors import CORS

from app.config import DevelopmentConfig
from app.db import db

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_object(DevelopmentConfig)

    app.config["JWT_SECRET_KEY"] = "your-secret-key"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = True
    app.config["JWT_COOKIE_HTTPONLY"] = True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
    app.config["JWT_CSRF_IN_COOKIES"] = True

    jwt = JWTManager(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    from app.routes.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
