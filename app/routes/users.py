import os
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from werkzeug.utils import secure_filename

from app import allowed_file, UPLOAD_FOLDER
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from werkzeug.security import check_password_hash, generate_password_hash

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
        user_data["teacher_id"] = teacher.user_id
    else:
        user_data["role_teacher"] = 0

    if student:
        user_data["role_student"] = 1
        user_data["class_number"] = student.class_number
        user_data["school_name"] = student.school_name
        user_data["student_id"] = student.user_id
    else:
        user_data["role_student"] = 0

    if parent:
        user_data["role_parent"] = 1
        user_data["work_name"] = parent.work_name
        user_data["work_phone"] = parent.work_phone
        user_data["parent_id"] = parent.user_id
    else:
        user_data["role_parent"] = 0

    if administrator:
        user_data["role_administrator"] = 1
        user_data["access_level"] = administrator.access_level
        user_data["administrator_id"] = administrator.Users_user_id
    else:
        user_data["role_administrator"] = 0

    return jsonify(user_data)


@users_bp.route('/update_self', methods=['PUT'])
@jwt_required()
def update_self():
    user_id = get_jwt_identity()
    update_data = request.get_json()

    if not update_data:
        return jsonify({"message": "No data provided"}), 400

    allowed_fields = {
        'full_name', 'email', 'birthday', 'gender',
        'city', 'phone_number', 'profile_picture_url', 'password'
    }

    filtered_data = {
        k: v for k, v in update_data.items()
        if k in allowed_fields
    }

    if not filtered_data:
        return jsonify({"message": "No valid fields to update"}), 400

    updated_user = repo.update_user(user_id, filtered_data)

    if not updated_user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "message": "User updated successfully",
        "user_id": updated_user.user_id,
        "updated_fields": list(filtered_data.keys())
    }), 200

@users_bp.route('/update_password', methods=['PUT'])
@jwt_required()
def update_password():
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'current_password', 'new_password'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Current and new password are required"}), 400

    user = repo.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password_hash, data['current_password']):
        return jsonify({"message": "Current password is incorrect"}), 401

    new_password_hash = generate_password_hash(data['new_password'])

    if not repo.update_user(user_id, {'password_hash': new_password_hash}):
        return jsonify({"message": "Failed to update password"}), 500

    return jsonify({
        "message": "Password updated successfully",
        "user_id": user_id
    }), 200


@users_bp.route('/upload_profile_picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "Allowed file types are: png, jpg, jpeg, gif"}), 400

    user_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    filename = secure_filename('avatar.' + file.filename.rsplit('.', 1)[1].lower())
    filepath = os.path.join(user_folder, filename)

    file.save(filepath)

    profile_url = f"/{UPLOAD_FOLDER}/{user_id}/{filename}"

    repo.update_user(user_id, {'profile_picture_url': profile_url})

    return jsonify({
        "message": "Profile picture uploaded successfully",
        "profile_picture_url": profile_url
    }), 200


@users_bp.route('/get_profile_picture', methods=['GET'])
@jwt_required()
def get_profile_picture():
    user_id = get_jwt_identity()
    user = repo.get_user_by_id(user_id)

    if not user or not user.profile_picture_url:
        return jsonify({"message": "User or profile picture not found"}), 404

    try:
        relative_path = user.profile_picture_url.lstrip('/')
        file_path = os.path.join(current_app.root_path, relative_path)

        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            return jsonify({"message": "Profile picture file not found"}), 404

        return send_from_directory(directory, filename)

    except Exception as e:
        current_app.logger.error(f"Error serving profile picture: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500


@users_bp.route('/get_by_unique_code/<string:unique_code>', methods=['GET'])
@jwt_required()
def get_user_by_unique_code(unique_code):

    current_user_id = get_jwt_identity()
    current_user = repo.get_user_by_id(current_user_id)

    if not current_user:
        return jsonify({"message": "Current user not found"}), 404

    user = repo.get_user_by_unique_code(unique_code)
    if not user:
        return jsonify({"message": "User with this unique code not found"}), 404

    student = repo_roles.get_student_by_user_id(user.user_id)
    if not student:
        return jsonify({"message": "This user is not a student"}), 404

    user_data = {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "gender": user.gender,
        "city": user.city,
        "phone_number": user.phone_number,
        "unique_code": user.unique_code,
        "profile_picture_url": user.profile_picture_url,
        "student_id": user.student.user_id
    }

    return jsonify(user_data), 200


@users_bp.route('/get_profile_picture_by_url', methods=['GET'])
def get_profile_picture_by_url():
    profile_picture_url = request.args.get('url')
    if not profile_picture_url:
        return jsonify({"message": "Profile picture URL is required"}), 400

    try:
        if not profile_picture_url.startswith('/uploads/'):
            return jsonify({"message": "Invalid URL format"}), 400

        relative_path = profile_picture_url.lstrip('/')
        path_parts = relative_path.split('/')

        safe_path_parts = []
        for part in path_parts:
            safe_part = secure_filename(part)
            if not safe_part or safe_part != part:
                return jsonify({"message": "Invalid path characters"}), 400
            safe_path_parts.append(safe_part)

        safe_relative_path = os.path.join(*safe_path_parts)
        file_path = os.path.join(current_app.root_path, safe_relative_path)

        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        if not os.path.abspath(file_path).startswith(os.path.abspath(uploads_dir)):
            return jsonify({"message": "Access denied"}), 403

        if os.path.exists(file_path):
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            return send_from_directory(directory, filename)

        default_image_path = os.path.join(current_app.root_path, 'uploads', 'default', 'profile', 'user.png')

        if not os.path.exists(default_image_path):
            return jsonify({"message": "Profile picture not found and default image is missing"}), 404

        return send_from_directory(
            os.path.dirname(default_image_path),
            os.path.basename(default_image_path)
        )

    except Exception as e:
        current_app.logger.error(f"Error serving profile picture by URL: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500