from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository, DisciplineRepository, UserRepository, AssociationTeacherStudentRepository
from app.db import db
from datetime import datetime

disciplines_bp = Blueprint('disciplines', __name__)

repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_users = UserRepository(db.session)


@disciplines_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_disciplines():
    try:
        disciplines = repo_disciplines.get_all_disciplines()
        disciplines_data = [{
            "discipline_id": d.discipline_id,
            "name": d.name,
            "description": d.description,
            "administrator_id": d.administrator_id,
            "created_at": d.created_at.isoformat()
        } for d in disciplines]

        return jsonify(disciplines_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/<int:discipline_id>', methods=['GET'])
@jwt_required()
def get_discipline(discipline_id):
    try:
        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        discipline_data = {
            "discipline_id": discipline.discipline_id,
            "name": discipline.name,
            "description": discipline.description,
            "administrator_id": discipline.administrator_id,
            "created_at": discipline.created_at.isoformat()
        }

        return jsonify(discipline_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/create', methods=['POST'])
@jwt_required()
def create_discipline():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'name', 'description'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can create disciplines"}), 403

        discipline = repo_disciplines.create_discipline(
            name=data['name'],
            description=data['description'],
            administrator_id=current_user_id
        )

        return jsonify({
            "message": "Discipline created successfully",
            "discipline_id": discipline.discipline_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/update/<int:discipline_id>', methods=['PUT'])
@jwt_required()
def update_discipline(discipline_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        if discipline.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        allowed_fields = {'name', 'description', 'administrator_id'}
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_discipline = repo_disciplines.update_discipline(
            discipline_id, **update_data
        )

        return jsonify({
            "message": "Discipline updated successfully",
            "discipline_id": updated_discipline.discipline_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/delete/<int:discipline_id>', methods=['DELETE'])
@jwt_required()
def delete_discipline(discipline_id):
    current_user_id = get_jwt_identity()

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can delete disciplines"}), 403

        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        if discipline.administrator_id != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        if repo_disciplines.delete_discipline(discipline_id):
            return jsonify({"message": "Discipline deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete discipline"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/administrator', methods=['GET'])
@jwt_required()
def get_administrator_disciplines():
    current_user_id = get_jwt_identity()

    try:
        disciplines = repo_disciplines.get_disciplines_by_administrator(current_user_id)
        disciplines_data = [{
            "discipline_id": d.discipline_id,
            "name": d.name,
            "description": d.description,
            "created_at": d.created_at.isoformat()
        } for d in disciplines]

        return jsonify(disciplines_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/teacher', methods=['GET'])
@jwt_required()
def get_teacher_disciplines():
    current_user_id = get_jwt_identity()

    try:
        disciplines = repo_disciplines.get_disciplines_for_teacher(current_user_id)
        disciplines_data = [{
            "discipline_id": d.discipline_id,
            "name": d.name,
            "description": d.description,
            "administrator_id": d.administrator_id
        } for d in disciplines]

        return jsonify(disciplines_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/<int:discipline_id>/teachers', methods=['GET'])
@jwt_required()
def get_discipline_teachers(discipline_id):
    try:
        teachers = repo_disciplines.get_teachers_for_discipline(discipline_id)
        teachers_data = [{
            "teacher_id": t.user_id,
            "full_name": t.user.full_name,
            "email": t.user.email
        } for t in teachers]

        return jsonify(teachers_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/<int:discipline_id>/add-teacher/<int:teacher_id>', methods=['POST'])
@jwt_required()
def add_teacher_to_discipline(discipline_id, teacher_id):
    current_user_id = get_jwt_identity()

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can add teacher to disciplines"}), 403

        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        if discipline.administrator_id != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        if repo_disciplines.check_teacher_discipline_association(teacher_id, discipline_id):
            return jsonify({"message": "Teacher already associated with this discipline"}), 400

        association = repo_disciplines.add_teacher_to_discipline(teacher_id, discipline_id)

        return jsonify({
            "message": "Teacher added to discipline successfully",
            "association_id": f"{teacher_id}_{discipline_id}"
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@disciplines_bp.route('/<int:discipline_id>/remove-teacher/<int:teacher_id>', methods=['DELETE'])
@jwt_required()
def remove_teacher_from_discipline(discipline_id, teacher_id):
    current_user_id = get_jwt_identity()

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can remove teacher to disciplines"}), 403

        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        if discipline.administrator_id != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        if not repo_disciplines.check_teacher_discipline_association(teacher_id, discipline_id):
            return jsonify({"message": "Teacher is not associated with this discipline"}), 400

        if repo_disciplines.remove_teacher_from_discipline(teacher_id, discipline_id):
            return jsonify({
                "message": "Teacher removed from discipline successfully"
            }), 200
        else:
            return jsonify({"message": "Failed to remove teacher from discipline"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500
