from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.repositories import TestRepository, DisciplineRepository, RoleRepository, UserRepository, RoleRepository
from app.db import db

tests_bp = Blueprint('tests', __name__)

repo_tests = TestRepository(db.session)
repo_disciplines = DisciplineRepository(db.session)
repo_users = UserRepository(db.session)
repo_roles = RoleRepository(db.session)


@tests_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_tests():
    try:
        tests = repo_tests.get_all_tests()
        tests_data = [{
            "test_id": t.test_id,
            "name": t.name,
            "description": t.description,
            "complexity": t.complexity,
            "discipline_id": t.discipline_id,
            "teacher_id": t.teacher_id
        } for t in tests]

        return jsonify(tests_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@tests_bp.route('/paginated', methods=['GET'])
@jwt_required()
def get_paginated_tests():
    current_user_id = get_jwt_identity()
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        tests, meta = repo_tests.get_paginated_tests(page=page, per_page=per_page)

        tests_data = [{
            "test_id": t.test_id,
            "name": t.name,
            "description": t.description,
            "complexity": t.complexity,
            "discipline_id": t.discipline_id,
            "teacher_full_name": t.teacher.user.full_name,
            "discipline_name": t.discipline.name,
            "to_edit": '1' if int(current_user_id) == t.teacher_id else '0',
            "teacher_id": t.teacher_id
        } for t in tests]

        return jsonify({
            "data": tests_data,
            "pagination": meta
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@tests_bp.route('/<int:test_id>', methods=['GET'])
@jwt_required()
def get_test(test_id):
    try:
        test = repo_tests.get_test_by_id(test_id)
        if not test:
            return jsonify({"message": "Test not found"}), 404

        test_data = {
            "test_id": test.test_id,
            "name": test.name,
            "description": test.description,
            "complexity": test.complexity,
            "discipline_id": test.discipline_id,
            "teacher_id": test.teacher_id,
            "discipline_name": test.discipline.name if test.discipline else None,
            "teacher_name": test.teacher.user.full_name if test.teacher else None
        }

        return jsonify(test_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/create', methods=['POST'])
@jwt_required()
def create_test():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'name', 'complexity', 'discipline_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        user = repo_users.get_user_by_id(current_user_id)
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)

        if not user or not teacher:
            return jsonify({"message": "Only teachers can create tests"}), 403

        discipline = repo_disciplines.get_discipline_by_id(data['discipline_id'])
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        if not repo_disciplines.check_teacher_discipline_association(current_user_id, data['discipline_id']):
            return jsonify({"message": "Teacher is not associated with this discipline"}), 403

        test = repo_tests.create_test(
            name=data['name'],
            complexity=data['complexity'],
            discipline_id=data['discipline_id'],
            teacher_id=current_user_id,
            description=data.get('description')
        )

        return jsonify({
            "message": "Test created successfully",
            "test_id": test.test_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/update/<int:test_id>', methods=['PUT'])
@jwt_required()
def update_test(test_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        test = repo_tests.get_test_by_id(test_id)
        if not test:
            return jsonify({"message": "Test not found"}), 404

        if test.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        allowed_fields = {'name', 'description', 'complexity', 'discipline_id'}
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if 'discipline_id' in update_data:
            if not repo_disciplines.check_teacher_discipline_association(current_user_id, update_data['discipline_id']):
                return jsonify({"message": "Teacher is not associated with this discipline"}), 403

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_test = repo_tests.update_test(test_id, **update_data)

        return jsonify({
            "message": "Test updated successfully",
            "test_id": updated_test.test_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/delete/<int:test_id>', methods=['DELETE'])
@jwt_required()
def delete_test(test_id):
    current_user_id = get_jwt_identity()

    try:
        test = repo_tests.get_test_by_id(test_id)
        if not test:
            return jsonify({"message": "Test not found"}), 404

        user = repo_users.get_user_by_id(current_user_id)
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)

        is_author = test.teacher_id == int(current_user_id)
        is_admin = repo_roles.get_administrator_by_user_id(current_user_id) is not None

        if not user or (not teacher and not is_admin):
            return jsonify({"message": "Access denied"}), 403

        if not is_author and not is_admin:
            return jsonify({"message": "Only test author or administrator can delete test"}), 403

        if repo_tests.delete_test(test_id):
            return jsonify({"message": "Test deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete test"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/teacher', methods=['GET'])
@jwt_required()
def get_teacher_tests():
    current_user_id = get_jwt_identity()

    try:
        tests = repo_tests.get_tests_by_teacher(current_user_id)
        tests_data = []

        for t in tests:
            exercises = repo_tests.get_exercises_for_test(t.test_id)

            tests_data.append({
                "test_id": t.test_id,
                "name": t.name,
                "description": t.description,
                "complexity": t.complexity,
                "discipline_id": t.discipline_id,
                "discipline_name": t.discipline.name if t.discipline else None,
                "exercises_count": len(exercises)
            })

        return jsonify(tests_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/discipline/<int:discipline_id>', methods=['GET'])
@jwt_required()
def get_discipline_tests(discipline_id):
    try:
        tests = repo_tests.get_tests_by_discipline(discipline_id)
        tests_data = [{
            "test_id": t.test_id,
            "name": t.name,
            "description": t.description,
            "complexity": t.complexity,
            "teacher_id": t.teacher_id,
            "teacher_name": t.teacher.user.full_name if t.teacher else None
        } for t in tests]

        return jsonify(tests_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/<int:test_id>/exercises', methods=['GET'])
@jwt_required()
def get_test_exercises(test_id):
    current_user_id = get_jwt_identity()

    try:
        exercises = repo_tests.get_exercises_for_test(test_id)
        exercises_data = [{
            "exercise_id": e.exercise_id,
            "name": e.name,
            "description": e.description,
            "verification_type": e.verification_type,
            "max_score": e.max_score,
            "module_id": e.module_id,
            "created_at": e.created_at,
            "right_answer": e.right_answer,
            "teacher_full_name": e.teacher.user.full_name,
            "module_name": e.module.description,
            "classifier_name": e.module.classifier.name,
            "discipline_name": e.module.classifier.discipline.name,
            "to_edit": '1' if int(current_user_id) == e.teacher_id else '0',
        } for e in exercises]

        return jsonify(exercises_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/<int:test_id>/add-exercise/<int:exercise_id>', methods=['POST'])
@jwt_required()
def add_exercise_to_test(test_id, exercise_id):
    current_user_id = get_jwt_identity()

    try:
        test = repo_tests.get_test_by_id(test_id)
        if not test:
            return jsonify({"message": "Test not found"}), 404

        if test.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_tests.check_exercise_in_test(test_id, exercise_id):
            return jsonify({"message": "Exercise already in test"}), 400

        association = repo_tests.add_exercise_to_test(test_id, exercise_id)

        return jsonify({
            "message": "Exercise added to test successfully",
            "association_id": f"{test_id}_{exercise_id}"
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@tests_bp.route('/<int:test_id>/remove-exercise/<int:exercise_id>', methods=['DELETE'])
@jwt_required()
def remove_exercise_from_test(test_id, exercise_id):
    current_user_id = get_jwt_identity()

    try:
        test = repo_tests.get_test_by_id(test_id)
        if not test:
            return jsonify({"message": "Test not found"}), 404

        if test.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if not repo_tests.check_exercise_in_test(test_id, exercise_id):
            return jsonify({"message": "Exercise not in test"}), 400

        if repo_tests.remove_exercise_from_test(test_id, exercise_id):
            return jsonify({"message": "Exercise removed from test successfully"}), 200
        else:
            return jsonify({"message": "Failed to remove exercise from test"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500