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

education_exercise_bp = Blueprint('education_exercises', __name__)

@education_exercise_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_exercises():
    current_user_id = get_jwt_identity()
    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers get exercises"}), 403

        exercises = repo_exercises.get_all_exercises()
        exercises_data = [{
            "exercise_id": e.exercise_id,
            "name": e.name,
            "description": e.description,
            "verification_type": e.verification_type,
            "right_answer": e.right_answer,
            "max_score": e.max_score,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "module_id": e.module_id,
            "teacher_id": e.teacher_id
        } for e in exercises]

        return jsonify(exercises_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_exercise_bp.route('/<int:exercise_id>', methods=['GET'])
@jwt_required()
def get_exercise(exercise_id):
    current_user_id = get_jwt_identity()
    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers get exercises"}), 403

        exercise = repo_exercises.get_exercise_by_id(exercise_id)
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404

        exercise_data = {
            "exercise_id": exercise.exercise_id,
            "name": exercise.name,
            "description": exercise.description,
            "verification_type": exercise.verification_type,
            "right_answer": exercise.right_answer,
            "max_score": exercise.max_score,
            "created_at": exercise.created_at.isoformat() if exercise.created_at else None,
            "module_id": exercise.module_id,
            "teacher_id": exercise.teacher_id
        }

        return jsonify(exercise_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_exercise_bp.route('/create', methods=['POST'])
@jwt_required()
def create_exercise():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {'name', 'description', 'verification_type', 'max_score', 'module_id'}
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can create exercises"}), 403

        exercise = repo_exercises.create_exercise(
            name=data['name'],
            description=data['description'],
            verification_type=data['verification_type'],
            max_score=data['max_score'],
            module_id=data['module_id'],
            teacher_id=current_user_id,
            right_answer=data.get('right_answer')
        )

        return jsonify({
            "message": "Exercise created successfully",
            "exercise_id": exercise.exercise_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_exercise_bp.route('/update/<int:exercise_id>', methods=['PUT'])
@jwt_required()
def update_exercise(exercise_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        exercise = repo_exercises.get_exercise_by_id(exercise_id)
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404

        if exercise.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'verification_type' in data:
            update_data['verification_type'] = data['verification_type']
        if 'right_answer' in data:
            update_data['right_answer'] = data['right_answer']
        if 'max_score' in data:
            update_data['max_score'] = data['max_score']
        if 'module_id' in data:
            update_data['module_id'] = data['module_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_exercise = repo_exercises.update_exercise(exercise_id, **update_data)

        return jsonify({
            "message": "Exercise updated successfully",
            "exercise_id": updated_exercise.exercise_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_exercise_bp.route('/delete/<int:exercise_id>', methods=['DELETE'])
@jwt_required()
def delete_exercise(exercise_id):
    current_user_id = get_jwt_identity()

    try:
        exercise = repo_exercises.get_exercise_by_id(exercise_id)
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404

        if exercise.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_exercises.delete_exercise(exercise_id):
            return jsonify({"message": "Exercise deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete exercise"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@education_exercise_bp.route('/module/<int:module_id>', methods=['GET'])
@jwt_required()
def get_exercises_by_module(module_id):
    current_user_id = get_jwt_identity()

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers get exercises"}), 403

        exercises = repo_exercises.get_exercises_by_module(module_id)
        exercises_data = [{
            "exercise_id": e.exercise_id,
            "name": e.name,
            "description": e.description,
            "verification_type": e.verification_type,
            "max_score": e.max_score
        } for e in exercises]

        return jsonify(exercises_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@education_exercise_bp.route('/filtered', methods=['GET'])
@jwt_required()
def get_filtered_exercises():
    current_user_id = get_jwt_identity()

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers get exercises"}), 403

        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        discipline_id = request.args.get('discipline_id', type=int)
        classifier_id = request.args.get('classifier_id', type=int)
        module_id = request.args.get('module_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)

        exercises, total = repo_exercises.get_filtered_exercises(
            page=page,
            per_page=per_page,
            discipline_id=discipline_id,
            classifier_id=classifier_id,
            module_id=module_id,
            teacher_id=teacher_id
        )

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

        return jsonify({
            "data": exercises_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@education_exercise_bp.route('/discipline/<int:discipline_id>', methods=['GET'])
@jwt_required()
def get_exercises_by_discipline(discipline_id):
    current_user_id = get_jwt_identity()

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can get exercises"}), 403

        discipline = repo_disciplines.get_discipline_by_id(discipline_id)
        if not discipline:
            return jsonify({"message": "Discipline not found"}), 404

        exercises = repo_exercises.get_exercises_by_discipline(discipline_id)
        exercises_data = [{
            "exercise_id": e.exercise_id,
            "name": e.name,
            "description": e.description,
            "verification_type": e.verification_type,
            "max_score": e.max_score,
            "module_id": e.module_id,
            "right_answer": e.right_answer,
            "module_name": e.module.description if e.module else None,
            "teacher_id": e.teacher_id,
            "classifier_name": e.module.classifier.name,
            "discipline_name": e.module.classifier.discipline.name,
            "teacher_full_name": e.teacher.user.full_name if e.teacher else None,
            "created_at": e.created_at.isoformat() if e.created_at else None
        } for e in exercises]

        return jsonify(exercises_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500