from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository, DisciplineRepository, \
    UserRepository, AssociationTeacherStudentRepository, BranchRepository, ClassroomRepository
from app.db import db
from datetime import datetime, time

branches_bp = Blueprint('branches', __name__)

repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_branches = BranchRepository(db.session)
repo_classrooms = ClassroomRepository(db.session)
repo_users = UserRepository(db.session)


@branches_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_branches():
    try:
        branches = repo_branches.get_all_branches()
        branches_data = [{
            "branch_id": b.branch_id,
            "address": b.address,
            "working_start": b.working_start.isoformat() if b.working_start else None,
            "working_end": b.working_end.isoformat() if b.working_end else None,
            "description": b.description,
            "photo_url": b.photo_url,
            "administrator_id": b.administrator_id,
            "updated_at": b.updated_at.isoformat()
        } for b in branches]

        return jsonify(branches_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@branches_bp.route('/<int:branch_id>', methods=['GET'])
@jwt_required()
def get_branch(branch_id):
    try:
        branch = repo_branches.get_branch_by_id(branch_id)
        if not branch:
            return jsonify({"message": "Branch not found"}), 404

        branch_data = {
            "branch_id": branch.branch_id,
            "address": branch.address,
            "working_start": branch.working_start.isoformat() if branch.working_start else None,
            "working_end": branch.working_end.isoformat() if branch.working_end else None,
            "description": branch.description,
            "photo_url": branch.photo_url,
            "administrator_id": branch.administrator_id,
            "updated_at": branch.updated_at.isoformat()
        }

        return jsonify(branch_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@branches_bp.route('/create', methods=['POST'])
@jwt_required()
def create_branch():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'working_start', 'working_end'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        user = repo_users.get_user_by_id(current_user_id)
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)

        if not user or not administrator:
            return jsonify({"message": "Only administrators can create branches"}), 403

        branch = repo_branches.create_branch(
            address=data.get('address'),
            working_start=time.fromisoformat(data['working_start']),
            working_end=time.fromisoformat(data['working_end']),
            description=data.get('description'),
            photo_url=data.get('photo_url'),
            administrator_id=current_user_id
        )

        return jsonify({
            "message": "Branch created successfully",
            "branch_id": branch.branch_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@branches_bp.route('/update/<int:branch_id>', methods=['PUT'])
@jwt_required()
def update_branch(branch_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        branch = repo_branches.get_branch_by_id(branch_id)
        if not branch:
            return jsonify({"message": "Branch not found"}), 404

        if branch.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'address' in data:
            update_data['address'] = data['address']
        if 'working_start' in data:
            update_data['working_start'] = time.fromisoformat(data['working_start'])
        if 'working_end' in data:
            update_data['working_end'] = time.fromisoformat(data['working_end'])
        if 'description' in data:
            update_data['description'] = data['description']
        if 'photo_url' in data:
            update_data['photo_url'] = data['photo_url']
        if 'administrator_id' in data:
            update_data['administrator_id'] = data['administrator_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_branch = repo_branches.update_branch(branch_id, **update_data)

        return jsonify({
            "message": "Branch updated successfully",
            "branch_id": updated_branch.branch_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@branches_bp.route('/delete/<int:branch_id>', methods=['DELETE'])
@jwt_required()
def delete_branch(branch_id):
    current_user_id = get_jwt_identity()

    try:
        branch = repo_branches.get_branch_by_id(branch_id)
        if not branch:
            return jsonify({"message": "Branch not found"}), 404

        if branch.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_branches.delete_branch(branch_id):
            return jsonify({"message": "Branch deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete branch"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@branches_bp.route('/administrator', methods=['GET'])
@jwt_required()
def get_administrator_branches():
    current_user_id = get_jwt_identity()

    try:
        branches = repo_branches.get_branches_by_administrator(current_user_id)
        branches_data = [{
            "branch_id": b.branch_id,
            "address": b.address,
            "working_start": b.working_start.isoformat() if b.working_start else None,
            "working_end": b.working_end.isoformat() if b.working_end else None,
            "description": b.description,
            "photo_url": b.photo_url
        } for b in branches]

        return jsonify(branches_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

