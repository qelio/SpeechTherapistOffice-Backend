from flask import request, jsonify
from flask import Blueprint
from werkzeug.security import check_password_hash
from app.models import User
from app.db import db
from ..repositories import UserRepository
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity
)

from ..utils.generate_unique_code import generate_unique_code

repo = UserRepository(db.session)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        required_fields = ['full_name', 'email', 'password', 'birthday', 'gender', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Не все обязательные поля заполнены"}), 400

        try:
            data['birthday'] = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Некорректный формат даты. Используйте YYYY-MM-DD"}), 400

        data['unique_code'] = generate_unique_code()
        user = repo.create_user_with_role(data)

        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        response = jsonify({
            "message": "Пользователь успешно зарегистрирован",
            "user_id": user.user_id,
            "role": data['role']
        })

        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response


    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = repo.authenticate_user(data.get('email'), data.get('password'))
    print(data.get('email'), data.get('password'))

    if not user:
        return jsonify({"error": "Неверный email или пароль"}), 401

    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    response = jsonify({"user_id": user.user_id})
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({"msg": "Успешный выход"})
    unset_jwt_cookies(response)
    return response

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    response = jsonify({"msg": "Access token update"})
    set_access_cookies(response, new_access_token)
    return response

@auth_bp.route('/check_auth', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    return jsonify({"user_id": user_id})