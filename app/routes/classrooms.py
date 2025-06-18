from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository, DisciplineRepository, \
    UserRepository, AssociationTeacherStudentRepository, BranchRepository, ClassroomRepository
from app.db import db
from datetime import datetime, time

classrooms_bp = Blueprint('classrooms', __name__)

repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_branches = BranchRepository(db.session)
repo_classrooms = ClassroomRepository(db.session)
repo_users = UserRepository(db.session)


@classrooms_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_classrooms():
    try:
        classrooms = repo_classrooms.get_all_classrooms()
        classrooms_data = [{
            "classroom_id": c.classroom_id,
            "name": c.name,
            "description": c.description,
            "branch_id": c.branch_id,
            "administrator_id": c.administrator_id,
            "updated_at": c.updated_at.isoformat()
        } for c in classrooms]

        return jsonify(classrooms_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/<int:classroom_id>', methods=['GET'])
@jwt_required()
def get_classroom(classroom_id):
    try:
        classroom = repo_classrooms.get_classroom_by_id(classroom_id)
        if not classroom:
            return jsonify({"message": "Classroom not found"}), 404

        classroom_data = {
            "classroom_id": classroom.classroom_id,
            "name": classroom.name,
            "description": classroom.description,
            "branch_id": classroom.branch_id,
            "administrator_id": classroom.administrator_id,
            "updated_at": classroom.updated_at.isoformat()
        }

        return jsonify(classroom_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/create', methods=['POST'])
@jwt_required()
def create_classroom():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'name', 'branch_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can create classrooms"}), 403

        classroom = repo_classrooms.create_classroom(
            name=data['name'],
            branch_id=data['branch_id'],
            administrator_id=current_user_id,
            description=data.get('description')
        )

        return jsonify({
            "message": "Classroom created successfully",
            "classroom_id": classroom.classroom_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/update/<int:classroom_id>', methods=['PUT'])
@jwt_required()
def update_classroom(classroom_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        classroom = repo_classrooms.get_classroom_by_id(classroom_id)
        if not classroom:
            return jsonify({"message": "Classroom not found"}), 404

        if classroom.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'branch_id' in data:
            update_data['branch_id'] = data['branch_id']
        if 'administrator_id' in data:
            update_data['administrator_id'] = data['administrator_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_classroom = repo_classrooms.update_classroom(classroom_id, **update_data)

        return jsonify({
            "message": "Classroom updated successfully",
            "classroom_id": updated_classroom.classroom_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/delete/<int:classroom_id>', methods=['DELETE'])
@jwt_required()
def delete_classroom(classroom_id):
    current_user_id = get_jwt_identity()

    try:
        classroom = repo_classrooms.get_classroom_by_id(classroom_id)
        if not classroom:
            return jsonify({"message": "Classroom not found"}), 404

        if classroom.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_classrooms.delete_classroom(classroom_id):
            return jsonify({"message": "Classroom deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete classroom"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/branch/<int:branch_id>', methods=['GET'])
@jwt_required()
def get_classrooms_by_branch(branch_id):
    try:
        classrooms = repo_classrooms.get_classrooms_by_branch(branch_id)
        classrooms_data = [{
            "classroom_id": c.classroom_id,
            "name": c.name,
            "description": c.description,
            "administrator_id": c.administrator_id
        } for c in classrooms]

        return jsonify(classrooms_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@classrooms_bp.route('/administrator', methods=['GET'])
@jwt_required()
def get_administrator_classrooms():
    current_user_id = get_jwt_identity()

    try:
        classrooms = repo_classrooms.get_classrooms_by_administrator(current_user_id)
        classrooms_data = [{
            "classroom_id": c.classroom_id,
            "name": c.name,
            "description": c.description,
            "branch_id": c.branch_id
        } for c in classrooms]

        return jsonify(classrooms_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500