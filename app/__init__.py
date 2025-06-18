import os

from flask_jwt_extended import JWTManager
from flask import Flask
from flask_migrate import Migrate
from datetime import timedelta
from flask_cors import CORS

from app.config import DevelopmentConfig
from app.db import db
from werkzeug.utils import secure_filename
from app.tasks.scheduler import init_scheduler

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads/users'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    jwt = JWTManager(app)

    init_scheduler(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    from app.routes.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.associations import association_bp
    app.register_blueprint(association_bp, url_prefix='/associations')

    from app.routes.subscriptions import subscriptions_bp
    app.register_blueprint(subscriptions_bp, url_prefix='/subscriptions')

    from app.routes.disciplines import disciplines_bp
    app.register_blueprint(disciplines_bp, url_prefix='/disciplines')

    from app.routes.branches import branches_bp
    app.register_blueprint(branches_bp, url_prefix='/branches')

    from app.routes.classrooms import classrooms_bp
    app.register_blueprint(classrooms_bp, url_prefix='/classrooms')

    from app.routes.lessons import lessons_bp
    app.register_blueprint(lessons_bp, url_prefix='/lessons')

    from app.routes.education_classifiers import education_classifier_bp
    app.register_blueprint(education_classifier_bp, url_prefix='/education_classifiers')

    from app.routes.education_modules import education_module_bp
    app.register_blueprint(education_module_bp, url_prefix='/education_modules')

    from app.routes.education_exercises import education_exercise_bp
    app.register_blueprint(education_exercise_bp, url_prefix='/education_exercises')

    from app.routes.tests import tests_bp
    app.register_blueprint(tests_bp, url_prefix='/tests')

    from app.routes.test_packages import test_packages_bp
    app.register_blueprint(test_packages_bp, url_prefix='/test_packages')

    from app.routes.active_tests import active_tests_bp
    app.register_blueprint(active_tests_bp, url_prefix='/active_tests')

    return app
