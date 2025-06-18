from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.repositories import (
    ActiveTestRepository,
    TestRepository,
    UserRepository,
    RoleRepository,
    LessonRepository, AssociationTeacherStudentRepository, TestPackageRepository
)
from app.db import db

active_tests_bp = Blueprint('active_tests', __name__)

repo_active_tests = ActiveTestRepository(db.session)
repo_tests = TestRepository(db.session)
repo_users = UserRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_associations = AssociationTeacherStudentRepository(db.session)
repo_test_packages = TestPackageRepository(db.session)


@active_tests_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_active_tests():
    try:
        current_user_id = get_jwt_identity()
        user = repo_users.get_user_by_id(current_user_id)

        if repo_roles.get_administrator_by_user_id(current_user_id):
            active_tests = repo_active_tests.get_all_active_tests()
        elif repo_roles.get_teacher_by_user_id(current_user_id):
            active_tests = repo_active_tests.get_active_tests_by_teacher(current_user_id)
        else:
            active_tests = repo_active_tests.get_active_tests_by_student(current_user_id)

        active_tests_data = [{
            "active_id": at.active_id,
            "test_id": at.test_id,
            "test_name": at.test.name if at.test else None,
            "student_id": at.student_id,
            "student_name": at.student.user.full_name if at.student else None,
            "teacher_id": at.teacher_id,
            "teacher_name": at.teacher.user.full_name if at.teacher else None,
            "status": at.status,
            "time_start": at.time_start.isoformat() if at.time_start else None,
            "time_end": at.time_end.isoformat() if at.time_end else None,
            "assessment": at.assessment,
            "lesson_id": at.lesson_id
        } for at in active_tests]

        return jsonify(active_tests_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/<int:active_id>', methods=['GET'])
@jwt_required()
def get_active_test(active_id):
    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        current_user_id = get_jwt_identity()
        if not (current_user_id in [active_test.student_id, active_test.teacher_id] or
                repo_roles.get_administrator_by_user_id(current_user_id)):
            return jsonify({"message": "Access denied"}), 403

        active_test_data = {
            "active_id": active_test.active_id,
            "test_id": active_test.test_id,
            "test_name": active_test.test.name if active_test.test else None,
            "student_id": active_test.student_id,
            "student_name": active_test.student.user.full_name if active_test.student else None,
            "teacher_id": active_test.teacher_id,
            "teacher_name": active_test.teacher.user.full_name if active_test.teacher else None,
            "status": active_test.status,
            "time_start": active_test.time_start.isoformat() if active_test.time_start else None,
            "time_end": active_test.time_end.isoformat() if active_test.time_end else None,
            "assessment": active_test.assessment,
            "lesson_id": active_test.lesson_id,
            "packages": [{
                "package_id": p.package_id,
                "exercise_id": p.exercise_id,
                "exercise_name": p.exercise.name if p.exercise else None,
                "status_verification": p.status_verification,
                "accumulated_score": p.accumulated_score
            } for p in active_test.packages]
        }

        return jsonify(active_test_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/create', methods=['POST'])
@jwt_required()
def create_active_test():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'test_id', 'student_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can create active tests"}), 403

        test = repo_tests.get_test_by_id(data['test_id'])
        if not test or test.teacher_id != int(current_user_id):
            return jsonify({"message": "Test not found or access denied"}), 404

        student = repo_roles.get_student_by_user_id(data['student_id'])
        if not student:
            return jsonify({"message": "Student not found"}), 404

        active_test = repo_active_tests.create_active_test(
            test_id=data['test_id'],
            student_id=data['student_id'],
            teacher_id=current_user_id,
            lesson_id=data.get('lesson_id'),
            status=data.get('status', 'active_not_sent')
        )

        return jsonify({
            "message": "Active test created successfully",
            "active_id": active_test.active_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/start/<int:active_id>', methods=['POST'])
@jwt_required()
def start_active_test(active_id):
    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        current_user_id = get_jwt_identity()
        if active_test.student_id != int(current_user_id):
            return jsonify({"message": "Only student can start the test"}), 403

        if not(active_test.time_start):
            updated_test = repo_active_tests.start_test(active_id)
        else:
            updated_test = active_test

        return jsonify({
            "message": "Test started successfully",
            "time_start": updated_test.time_start.isoformat()
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/complete/<int:active_id>', methods=['POST'])
@jwt_required()
def complete_active_test(active_id):
    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        current_user_id = get_jwt_identity()
        if active_test.student_id != int(current_user_id):
            return jsonify({"message": "Only student can complete the test"}), 403

        if not active_test.time_start:
            return jsonify({"message": "Test not started yet"}), 400

        if active_test.time_end:
            return jsonify({"message": "Test already completed"}), 400

        data = request.get_json()
        updated_test = repo_active_tests.complete_test(
            active_id,
            assessment=data.get('assessment')
        )

        return jsonify({
            "message": "Test completed successfully",
            "time_end": updated_test.time_end.isoformat(),
            "assessment": updated_test.assessment
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/teacher/unverified', methods=['GET'])
@jwt_required()
def get_unverified_packages():
    try:
        current_user_id = get_jwt_identity()
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Access denied"}), 403

        packages = repo_test_packages.get_unverified_packages(current_user_id)
        packages_data = [{
            "package_id": p.package_id,
            "active_id": p.active_id,
            "exercise_id": p.exercise_id,
            "exercise_name": p.exercise.name if p.exercise else None,
            "student_name": p.active_test.student.user.full_name if p.active_test.student else None,
            "exercise_start": p.exercise_start.isoformat() if p.exercise_start else None,
            "exercise_end": p.exercise_end.isoformat() if p.exercise_end else None,
            "student_answer": p.student_answer,
            "file_url": p.file_url
        } for p in packages]

        return jsonify(packages_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/<int:active_id>/stats', methods=['GET'])
@jwt_required()
def get_active_test_stats(active_id):
    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        current_user_id = get_jwt_identity()
        if not (current_user_id in [active_test.student_id, active_test.teacher_id] or
                repo_roles.get_administrator_by_user_id(current_user_id)):
            return jsonify({"message": "Access denied"}), 403

        stats = repo_active_tests.get_package_stats(active_id)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/<int:active_id>/packages', methods=['GET'])
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

        packages = repo_active_tests.get_packages_for_active_test(active_id)
        packages_data = [{
            "package_id": p.package_id,
            "exercise_id": p.exercise_id,
            "exercise_name": p.exercise.name if p.exercise else None,
            "status_verification": p.status_verification,
            "exercise_start": p.exercise_start.isoformat() if p.exercise_start else None,
            "exercise_end": p.exercise_end.isoformat() if p.exercise_end else None,
            "student_answer": p.student_answer,
            "file_url": p.file_url,
            "accumulated_score": p.accumulated_score,
            "max_score": p.exercise.max_score if p.exercise else None
        } for p in packages]

        return jsonify(packages_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@active_tests_bp.route('/<int:active_id>/add-package', methods=['POST'])
@jwt_required()
def add_package_to_active_test(active_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'exercise_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        if active_test.student_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        package = repo_active_tests.add_package_to_active_test(
            active_id=active_id,
            exercise_id=data['exercise_id'],
            student_answer=data.get('student_answer'),
            file_url=data.get('file_url')
        )

        return jsonify({
            "message": "Package added to active test successfully",
            "package_id": package.package_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@active_tests_bp.route('/package/<int:package_id>', methods=['PUT'])
@jwt_required()
def update_package(package_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        package = repo_test_packages.get_package_by_id(package_id)
        if not package:
            return jsonify({"message": "Package not found"}), 404

        if package.active_test.student_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        updated_package = repo_active_tests.update_package(
            package_id=package_id,
            status_verification=data.get('status_verification'),
            student_answer=data.get('student_answer'),
            file_url=data.get('file_url'),
            accumulated_score=data.get('accumulated_score'),
            complete=data.get('complete', False)
        )

        return jsonify({
            "message": "Package updated successfully",
            "package_id": updated_package.package_id
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@active_tests_bp.route('/package/<int:package_id>/verify', methods=['POST'])
@jwt_required()
def verify_package(package_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'score' not in data:
        return jsonify({"message": "Score is required"}), 400

    try:
        package = repo_test_packages.get_package_by_id(package_id)
        if not package:
            return jsonify({"message": "Package not found"}), 404

        if package.active_test.teacher_id != current_user_id:
            return jsonify({"message": "Only teacher can verify packages"}), 403

        verified_package = repo_active_tests.verify_package(
            package_id=package_id,
            score=data['score']
        )

        return jsonify({
            "message": "Package verified successfully",
            "package_id": verified_package.package_id,
            "score": verified_package.accumulated_score
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/my-tests-active', methods=['GET'])
@jwt_required()
def get_my_active_tests():
    current_user_id = get_jwt_identity()

    try:
        student = repo_roles.get_student_by_user_id(current_user_id)
        if not student:
            return jsonify({"message": "Only students can access their tests"}), 403

        active_tests = repo_active_tests.get_active_tests_by_student(current_user_id)

        active_tests_data = []
        for at in active_tests:
            test_exercises_count = repo_tests.get_exercises_count_by_test(at.test_id)

            student_packages_count = len(repo_active_tests.get_packages_for_active_test(at.active_id))
            if at.status == 'active_not_sent' and at.student_id == int(current_user_id):
                active_tests_data.append({
                    "active_id": at.active_id,
                    "test_id": at.test_id,
                    "test_name": at.test.name if at.test else None,
                    "status": at.status,
                    "time_start": at.time_start.isoformat() if at.time_start else None,
                    "time_end": at.time_end.isoformat() if at.time_end else None,
                    "assessment": at.assessment,
                    "teacher_name": at.teacher.user.full_name if at.teacher else None,
                    "test_complexity": at.test.complexity if at.test else None,
                    "discipline_name": at.test.discipline.name if at.test and at.test.discipline else None,
                    "total_exercises": test_exercises_count,
                    "completed_exercises": student_packages_count
                })

        return jsonify(active_tests_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@active_tests_bp.route('/my-completed-tests', methods=['GET'])
@jwt_required()
def get_my_completed_tests():
    current_user_id = get_jwt_identity()

    try:
        student = repo_roles.get_student_by_user_id(current_user_id)
        if not student:
            return jsonify({"message": "Only students can access their tests"}), 403

        completed_tests = repo_active_tests.get_completed_tests_by_student(current_user_id)
        tests_data = []

        for test in completed_tests:
            total_exercises = repo_tests.get_exercises_count_by_test(test.test_id)
            correct_answers = repo_active_tests.get_correct_answers_count(test.active_id)
            exercises = repo_active_tests.get_exercises_with_answers(test.active_id)

            tests_data.append({
                "active_id": test.active_id,
                "test_name": test.test.name,
                "discipline": test.test.discipline.name,
                "time_start": test.time_start.isoformat(),
                "time_end": test.time_end.isoformat(),
                "total_exercises": total_exercises,
                "correct_answers": correct_answers,
                "assessment": test.assessment,
                "teacher": test.teacher.user.full_name,
                "exercises": exercises
            })

        return jsonify(tests_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@active_tests_bp.route('/<int:active_id>/exercises', methods=['GET'])
@jwt_required()
def get_active_test_exercises(active_id):
    current_user_id = get_jwt_identity()

    try:
        active_test = repo_active_tests.get_active_test_by_id(active_id)
        if not active_test:
            return jsonify({"message": "Active test not found"}), 404

        if active_test.student_id != int(current_user_id):
            return jsonify({"message": "You can only view your own tests"}), 403

        test = repo_tests.get_test_by_id(active_test.test_id)
        if not test:
            return jsonify({"message": "Original test not found"}), 404

        exercises = repo_tests.get_exercises_for_test(test.test_id)

        student_packages = repo_active_tests.get_packages_for_active_test(active_id)
        package_dict = {p.exercise_id: p for p in student_packages}

        exercises_data = []
        for exercise in exercises:
            package = package_dict.get(exercise.exercise_id)

            exercises_data.append({
                "exercise_id": exercise.exercise_id,
                "name": exercise.name,
                "description": exercise.description,
                "verification_type": exercise.verification_type,
                "max_score": exercise.max_score,
                "right_answer": exercise.right_answer,
                "student_answer": package.student_answer if package else None,
                "status_verification": package.status_verification if package else "not_attempted",
                "attempted": package is not None
            })

        return jsonify({
            "test_id": test.test_id,
            "test_name": test.name,
            "exercises": exercises_data,
            "total_exercises": len(exercises),
            "completed_exercises": len(student_packages)
        }), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@active_tests_bp.route('/student-tests', methods=['GET'])
@jwt_required()
def get_student_tests():
    current_user_id = get_jwt_identity()

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can access this data"}), 403

        tests_data = repo_active_tests.get_teacher_student_tests(current_user_id)
        return jsonify(tests_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500