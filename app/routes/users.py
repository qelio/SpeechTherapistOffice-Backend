from flask import Blueprint, jsonify
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository

from app.db import db

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

users_bp = Blueprint('users', __name__)

repo = UserRepository(db.session)
repo_roles = RoleRepository(db.session)

@users_bp.route('/get_self', methods=['GET'])
@jwt_required()
def get_self():
    user_id = get_jwt_identity()
    user = repo.get_user_by_id(user_id)

    user_data = {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "gender": user.gender,
        "city": user.city,
        "phone_number": user.phone_number,
        "profile_picture_url": user.profile_picture_url,
        "unique_code": user.unique_code
    }

    teacher = repo_roles.get_teacher_by_user_id(user_id)
    student = repo_roles.get_student_by_user_id(user_id)
    parent = repo_roles.get_parent_by_user_id(user_id)
    administrator = repo_roles.get_administrator_by_user_id(user_id)

    if teacher:
        user_data["role_teacher"] = 1
        user_data["experience"] = teacher.experience
        user_data["main_work"] = teacher.main_work
    else:
        user_data["role_teacher"] = 0

    if student:
        user_data["role_student"] = 1
        user_data["class_number"] = student.class_number
        user_data["school_name"] = student.school_name
    else:
        user_data["role_student"] = 0

    if parent:
        user_data["role_parent"] = 1
        user_data["work_name"] = parent.work_name
        user_data["work_phone"] = parent.work_phone
    else:
        user_data["role_parent"] = 0

    if administrator:
        user_data["role_administrator"] = 1
        user_data["access_level"] = administrator.access_level
    else:
        user_data["role_administrator"] = 0


    return jsonify(user_data)


