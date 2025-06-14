from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import RoleRepository
from app.repositories.association_teacher_student_repository import AssociationTeacherStudentRepository
from app.repositories.user_repository import UserRepository
from app.db import db

association_bp = Blueprint('associations', __name__)
repo = AssociationTeacherStudentRepository(db.session)
user_repo = UserRepository(db.session)
role_repo = RoleRepository(db.session)


@association_bp.route('/teachers_for_current_student', methods=['GET'])
@jwt_required()
def get_teachers_for_current_student():
    current_user_id = get_jwt_identity()
    current_user = user_repo.get_user_by_id(current_user_id)

    if not current_user:
        return jsonify({"message": "User not found"}), 404

    student = role_repo.get_student_by_user_id(current_user_id)
    if not student:
        return jsonify({"message": "Current user is not a student"}), 403

    teachers = repo.get_teachers_for_student(student.user_id)
    return jsonify([{
        "user_id": teacher.user.user_id,
        "full_name": teacher.user.full_name,
        "email": teacher.user.email,
        "experience": teacher.experience,
        "main_work": teacher.main_work,
        "profile_picture_url": teacher.user.profile_picture_url
    } for teacher in teachers]), 200


@association_bp.route('/students_for_current_teacher', methods=['GET'])
@jwt_required()
def get_students_for_current_teacher():
    current_user_id = get_jwt_identity()
    current_user = user_repo.get_user_by_id(current_user_id)

    if not current_user:
        return jsonify({"message": "User not found"}), 404

    teacher = role_repo.get_teacher_by_user_id(current_user_id)
    if not teacher:
        return jsonify({"message": "Current user is not a teacher"}), 403

    students = repo.get_students_for_teacher(teacher.user_id)
    return jsonify([{
        "user_id": student.user.user_id,
        "full_name": student.user.full_name,
        "email": student.user.email,
        "birthday": student.user.birthday.isoformat() if student.user.birthday else None,
        "gender": student.user.gender,
        "city": student.user.city,
        "phone_number": student.user.phone_number,
        "unique_code": student.user.unique_code,
        "class_number": student.class_number,
        "school_name": student.school_name,
        "profile_picture_url": student.user.profile_picture_url
    } for student in students]), 200


@association_bp.route('/create', methods=['POST'])
@jwt_required()
def create_association():
    current_user_id = get_jwt_identity()
    current_user = user_repo.get_user_by_id(current_user_id)

    if not current_user or not current_user.teacher:
        return jsonify({"message": "Access denied or not a teacher"}), 403

    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({"message": "Student ID is required"}), 400

    try:
        association = repo.create_association(
            student_id=data['student_id'],
            teacher_id=current_user_id
        )
        return jsonify({
            "message": "Association created successfully",
            "student_id": association.student_user_id,
            "teacher_id": association.teacher_user_id
        }), 201
    except ValueError as e:
        return jsonify({"message": "The user is already linked to your profile"}), 400


@association_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_association():

    current_user_id = get_jwt_identity()
    current_user = user_repo.get_user_by_id(current_user_id)

    if not current_user or not current_user.teacher:
        return jsonify({"message": "Access denied or not a teacher"}), 403

    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({"message": "Student ID is required"}), 400

    if repo.delete_association(
            student_id=data['student_id'],
            teacher_id=current_user_id
    ):
        return jsonify({"message": "Association deleted successfully"}), 200
    else:
        return jsonify({"message": "Association not found"}), 404