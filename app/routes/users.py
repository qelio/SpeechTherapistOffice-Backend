from flask import Blueprint, jsonify
from app.repositories.user_repository import UserRepository
from app.db import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
def get_users():
    repo = UserRepository(db.session)
    users = repo.get_all_users()

    users_list = []
    for u in users:
        users_list.append({
            'user_id': u.user_id,
            'full_name': u.full_name,
            'email': u.email,
            'birthday': u.birthday.isoformat() if u.birthday else None,
            'gender': u.gender,
            'city': u.city,
            'phone_number': u.phone_number,
            'profile_picture_url': u.profile_picture_url,
            'unique_code': u.unique_code,
            'created_at': u.created_at.isoformat() if u.created_at else None,
        })

    return jsonify(users_list)
