from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.repositories import (
    TestPackageRepository,
    ActiveTestRepository,
    UserRepository,
    RoleRepository,
    EducationExerciseRepository
)
from app.db import db

test_packages_bp = Blueprint('test_packages', __name__)

repo_packages = TestPackageRepository(db.session)
repo_active_tests = ActiveTestRepository(db.session)
repo_users = UserRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_exercises = EducationExerciseRepository(db.session)

@test_packages_bp.route('/<int:package_id>', methods=['GET'])
@jwt_required()
def get_package(package_id):
    try:
        package = repo_packages.get_package_by_id(package_id)
        if not package:
            return jsonify({"message": "Package not found"}), 404

        current_user_id = get_jwt_identity()
        if not (current_user_id in [package.active_test.student_id, package.active_test.teacher_id] or
                repo_roles.get_administrator_by_user_id(current_user_id)):
            return jsonify({"message": "Access denied"}), 403

        package_data = {
            "package_id": package.package_id,
            "active_id": package.active_id,
            "exercise_id": package.exercise_id,
            "exercise_name": package.exercise.name if package.exercise else None,
            "status_verification": package.status_verification,
            "exercise_start": package.exercise_start.isoformat() if package.exercise_start else None,
            "exercise_end": package.exercise_end.isoformat() if package.exercise_end else None,
            "student_answer": package.student_answer,
            "file_url": package.file_url,
            "accumulated_score": package.accumulated_score,
            "max_score": package.exercise.max_score if package.exercise else None,
            "student_id": package.active_test.student_id,
            "teacher_id": package.active_test.teacher_id
        }

        return jsonify(package_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@test_packages_bp.route('/active/<int:active_id>', methods=['GET'])
@jwt_required()
def get_packages_for_active_test(active_id):
    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        current_user_id = get_jwt_identity()
        if not (current_user_id in [active_test.student_id, active_test.teacher_id] or
                repo_roles.get_administrator_by_user_id(current_user_id)):
            return jsonify({"message": "Access denied"}), 403

        packages = repo_packages.get_packages_by_active_test(active_id)
        packages_data = [{
            "package_id": p.package_id,
            "exercise_id": p.exercise_id,
            "exercise_name": p.exercise.name if p.exercise else None,
            "status_verification": p.status_verification,
            "exercise_start": p.exercise_start.isoformat() if p.exercise_start else None,
            "exercise_end": p.exercise_end.isoformat() if p.exercise_end else None,
            "accumulated_score": p.accumulated_score,
            "max_score": p.exercise.max_score if p.exercise else None
        } for p in packages]

        return jsonify(packages_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@test_packages_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_package():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'active_id', 'exercise_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        active_test = repo_active_tests.get_active_test_by_id(data['active_id'])
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        if active_test.student_id != current_user_id:
            return jsonify({"message": "Only student can submit packages"}), 403

        exercise = repo_exercises.get_exercise_by_id(data['exercise_id'])
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404

        package = repo_packages.create_package(
            active_id=data['active_id'],
            exercise_id=data['exercise_id'],
            student_answer=data.get('student_answer'),
            file_url=data.get('file_url')
        )

        return jsonify({
            "message": "Package submitted successfully",
            "package_id": package.package_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@test_packages_bp.route('/<int:package_id>/verify', methods=['POST'])
@jwt_required()
def verify_package(package_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'score' not in data:
        return jsonify({"message": "Score is required"}), 400

    try:
        package = repo_packages.get_package_by_id(package_id)
        if not package:
            return jsonify({"message": "Package not found"}), 404

        if package.active_test.teacher_id != current_user_id:
            return jsonify({"message": "Only teacher can verify packages"}), 403

        verified_package = repo_packages.verify_package(
            package_id=package_id,
            score=data['score'],
            status=data.get('status', 'verified')
        )

        return jsonify({
            "message": "Package verified successfully",
            "package_id": verified_package.package_id,
            "score": verified_package.accumulated_score,
            "status": verified_package.status_verification
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@test_packages_bp.route('/teacher/unverified', methods=['GET'])
@jwt_required()
def get_unverified_packages():
    try:
        current_user_id = get_jwt_identity()
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Access denied"}), 403

        packages = repo_packages.get_unverified_packages(current_user_id)
        packages_data = [{
            "package_id": p.package_id,
            "active_id": p.active_id,
            "exercise_id": p.exercise_id,
            "exercise_name": p.exercise.name if p.exercise else None,
            "student_name": p.active_test.student.user.full_name if p.active_test.student else None,
            "exercise_start": p.exercise_start.isoformat() if p.exercise_start else None,
            "exercise_end": p.exercise_end.isoformat() if p.exercise_end else None,
            "student_answer": p.student_answer,
            "file_url": p.file_url,
            "max_score": p.exercise.max_score if p.exercise else None
        } for p in packages]

        return jsonify(packages_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@test_packages_bp.route('/<int:package_id>', methods=['DELETE'])
@jwt_required()
def delete_package(package_id):
    try:
        package = repo_packages.get_package_by_id(package_id)
        if not package:
            return jsonify({"message": "Package not found"}), 404

        current_user_id = get_jwt_identity()
        is_teacher = package.active_test.teacher_id == current_user_id
        is_admin = repo_roles.get_administrator_by_user_id(current_user_id) is not None

        if not (is_teacher or is_admin):
            return jsonify({"message": "Access denied"}), 403

        if repo_packages.delete_package(package_id):
            return jsonify({"message": "Package deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete package"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500