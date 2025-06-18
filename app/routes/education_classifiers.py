from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import EducationClassifierRepository
from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository, DisciplineRepository, \
    UserRepository, AssociationTeacherStudentRepository, BranchRepository, ClassroomRepository
from app.db import db
from datetime import datetime, time

education_classifier_bp = Blueprint('education_classifiers', __name__)

repo_classifiers = EducationClassifierRepository(db.session)
repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_branches = BranchRepository(db.session)
repo_classrooms = ClassroomRepository(db.session)
repo_users = UserRepository(db.session)

@education_classifier_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_classifiers():
    try:
        classifiers = repo_classifiers.get_all_classifiers()
        classifiers_data = [{
            "classifier_id": c.classifier_id,
            "name": c.name,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "administrator_id": c.administrator_id,
            "discipline_id": c.discipline_id,
            "discipline_name": c.discipline.name
        } for c in classifiers]

        return jsonify(classifiers_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_classifier_bp.route('/<int:classifier_id>', methods=['GET'])
@jwt_required()
def get_classifier(classifier_id):
    try:
        classifier = repo_classifiers.get_classifier_by_id(classifier_id)
        if not classifier:
            return jsonify({"message": "Classifier not found"}), 404

        classifier_data = {
            "classifier_id": classifier.classifier_id,
            "name": classifier.name,
            "created_at": classifier.created_at.isoformat() if classifier.created_at else None,
            "administrator_id": classifier.administrator_id,
            "discipline_id": classifier.discipline_id,
            "discipline_name": classifier.discipline.name
        }

        return jsonify(classifier_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_classifier_bp.route('/create', methods=['POST'])
@jwt_required()
def create_classifier():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'name', 'discipline_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields: name and discipline_id"}), 400

    try:
        administrator = repo_roles.get_administrator_by_user_id(current_user_id)
        if not administrator:
            return jsonify({"message": "Only administrators can create classifiers"}), 403

        classifier = repo_classifiers.create_classifier(
            name=data['name'],
            administrator_id=current_user_id,
            discipline_id=data['discipline_id']
        )

        return jsonify({
            "message": "Classifier created successfully",
            "classifier_id": classifier.classifier_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_classifier_bp.route('/update/<int:classifier_id>', methods=['PUT'])
@jwt_required()
def update_classifier(classifier_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        classifier = repo_classifiers.get_classifier_by_id(classifier_id)
        if not classifier:
            return jsonify({"message": "Classifier not found"}), 404

        if classifier.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'discipline_id' in data:
            update_data['discipline_id'] = data['discipline_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_classifier = repo_classifiers.update_classifier(classifier_id, **update_data)

        return jsonify({
            "message": "Classifier updated successfully",
            "classifier_id": updated_classifier.classifier_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_classifier_bp.route('/delete/<int:classifier_id>', methods=['DELETE'])
@jwt_required()
def delete_classifier(classifier_id):
    current_user_id = get_jwt_identity()

    try:
        classifier = repo_classifiers.get_classifier_by_id(classifier_id)
        if not classifier:
            return jsonify({"message": "Classifier not found"}), 404

        if classifier.administrator_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_classifiers.delete_classifier(classifier_id):
            return jsonify({"message": "Classifier deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete classifier"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_classifier_bp.route('/discipline/<int:discipline_id>', methods=['GET'])
@jwt_required()
def get_classifiers_by_discipline(discipline_id):
    try:
        classifiers = repo_classifiers.get_classifiers_by_discipline(discipline_id)
        classifiers_data = [{
            "classifier_id": c.classifier_id,
            "name": c.name,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in classifiers]

        return jsonify(classifiers_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500