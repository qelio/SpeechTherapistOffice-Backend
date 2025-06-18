from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import EducationClassifierRepository
from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository, DisciplineRepository, \
    UserRepository, AssociationTeacherStudentRepository, BranchRepository, ClassroomRepository, EducationModuleRepository, EducationExerciseRepository
from app.db import db
from datetime import datetime, time

repo_classifiers = EducationClassifierRepository(db.session)
repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_branches = BranchRepository(db.session)
repo_classrooms = ClassroomRepository(db.session)
repo_users = UserRepository(db.session)
repo_modules = EducationModuleRepository(db.session)
repo_exercises = EducationExerciseRepository(db.session)

education_module_bp = Blueprint('education_modules', __name__)

@education_module_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_modules():
    current_user_id = get_jwt_identity()

    try:
        modules = repo_modules.get_all_modules()
        modules_data = [{
            "module_id": m.module_id,
            "description": m.description,
            "preview_url": m.preview_url,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "classifier_id": m.classifier_id,
            "teacher_id": m.teacher_id,
            "to_edit": '1' if int(current_user_id) == m.teacher_id else '0',
            "teacher_full_name": m.teacher.user.full_name,
            "classifier_name": m.classifier.name,
            "discipline_name": m.classifier.discipline.name,
        } for m in modules]

        return jsonify(modules_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_module_bp.route('/<int:module_id>', methods=['GET'])
@jwt_required()
def get_module(module_id):
    try:
        module = repo_modules.get_module_by_id(module_id)
        if not module:
            return jsonify({"message": "Module not found"}), 404

        module_data = {
            "module_id": module.module_id,
            "description": module.description,
            "preview_url": module.preview_url,
            "created_at": module.created_at.isoformat() if module.created_at else None,
            "classifier_id": module.classifier_id,
            "teacher_id": module.teacher_id
        }

        return jsonify(module_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_module_bp.route('/create', methods=['POST'])
@jwt_required()
def create_module():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'description', 'classifier_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields: description and classifier_id"}), 400

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can create modules"}), 403

        module = repo_modules.create_module(
            description=data['description'],
            classifier_id=data['classifier_id'],
            teacher_id=current_user_id,
            preview_url=data.get('preview_url')
        )

        return jsonify({
            "message": "Module created successfully",
            "module_id": module.module_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_module_bp.route('/update/<int:module_id>', methods=['PUT'])
@jwt_required()
def update_module(module_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        module = repo_modules.get_module_by_id(module_id)
        if not module:
            return jsonify({"message": "Module not found"}), 404

        if module.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'description' in data:
            update_data['description'] = data['description']
        if 'preview_url' in data:
            update_data['preview_url'] = data['preview_url']
        if 'classifier_id' in data:
            update_data['classifier_id'] = data['classifier_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_module = repo_modules.update_module(module_id, **update_data)

        return jsonify({
            "message": "Module updated successfully",
            "module_id": updated_module.module_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_module_bp.route('/delete/<int:module_id>', methods=['DELETE'])
@jwt_required()
def delete_module(module_id):
    current_user_id = get_jwt_identity()

    try:
        module = repo_modules.get_module_by_id(module_id)
        if not module:
            return jsonify({"message": "Module not found"}), 404

        if module.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_modules.delete_module(module_id):
            return jsonify({"message": "Module deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete module"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_module_bp.route('/classifier/<int:classifier_id>', methods=['GET'])
@jwt_required()
def get_modules_by_classifier(classifier_id):
    try:
        modules = repo_modules.get_modules_by_classifier(classifier_id)
        modules_data = [{
            "module_id": m.module_id,
            "description": m.description,
            "preview_url": m.preview_url,
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in modules]

        return jsonify(modules_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500