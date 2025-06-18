from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from sqlalchemy import select, func

from app.repositories import LessonRepository, RoleRepository, UserRepository, SubscriptionRepository
from app.db import db

lessons_bp = Blueprint('lessons', __name__)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)
repo_users = UserRepository(db.session)
repo_subscriptions = SubscriptionRepository(db.session)


@lessons_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_lessons():
    try:
        lessons = repo_lessons.get_all_lessons()
        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status,
            "teacher_id": l.teacher_id,
            "student_id": l.student_id,
            "subscription_id": l.subscription_id,
            "online_call_url": l.online_call_url,
            "classroom_id": l.classroom_id,
            "discipline_id": l.discipline_id,
            "created_at": l.created_at.isoformat()
        } for l in lessons]

        return jsonify(lessons_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_lesson(lesson_id):
    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        lesson_data = {
            "lesson_id": lesson.lesson_id,
            "lesson_date_time": lesson.lesson_date_time.isoformat(),
            "duration": lesson.duration,
            "status": lesson.status,
            "teacher_id": lesson.teacher_id,
            "student_id": lesson.student_id,
            "subscription_id": lesson.subscription_id,
            "online_call_url": lesson.online_call_url,
            "classroom_id": lesson.classroom_id,
            "created_at": lesson.created_at.isoformat()
        }

        return jsonify(lesson_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/create', methods=['POST'])
@jwt_required()
def create_lesson():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {
        'lesson_date_time',
        'duration',
        'status',
        'student_id'
    }

    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        admin = repo_roles.get_administrator_by_user_id(current_user_id)

        if not teacher and not admin:
            return jsonify({"message": "Only teachers or admins can create lessons"}), 403

        lesson = repo_lessons.create_lesson(
            lesson_date_time=datetime.fromisoformat(data['lesson_date_time']),
            duration=data['duration'],
            status=data['status'],
            teacher_id=current_user_id,
            student_id=data['student_id'],
            subscription_id=data.get('subscription_id'),
            online_call_url=data.get('online_call_url'),
            classroom_id=data.get('classroom_id'),
            discipline_id=data.get('discipline_id')
        )

        return jsonify({
            "message": "Lesson created successfully",
            "lesson_id": lesson.lesson_id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/update/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def update_lesson(lesson_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        update_data = {}
        if 'lesson_date_time' in data:
            update_data['lesson_date_time'] = datetime.fromisoformat(data['lesson_date_time'])
        if 'duration' in data:
            update_data['duration'] = data['duration']
        if 'status' in data:
            update_data['status'] = data['status']
        if 'online_call_url' in data:
            update_data['online_call_url'] = data['online_call_url']
        if 'subscription_id' in data:
            update_data['subscription_id'] = data['subscription_id']
        if 'classroom_id' in data:
            update_data['classroom_id'] = data['classroom_id']
        if 'discipline_id' in data:
            update_data['discipline_id'] = data['discipline_id']

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_lesson = repo_lessons.update_lesson(lesson_id, **update_data)

        return jsonify({
            "message": "Lesson updated successfully",
            "lesson_id": updated_lesson.lesson_id,
            "updated_fields": list(update_data.keys())
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_lessons(student_id):
    current_user_id = get_jwt_identity()

    try:
        if student_id != int(current_user_id) and not repo_roles.get_teacher_by_user_id(
                current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        lessons = repo_lessons.get_lessons_for_student(student_id)
        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status,
            "teacher_id": l.teacher_id,
            "subscription_id": l.subscription_id
        } for l in lessons]

        return jsonify(lessons_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
@jwt_required()
def get_teacher_lessons(teacher_id):
    current_user_id = get_jwt_identity()

    try:
        if teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        lessons = repo_lessons.get_lessons_for_teacher(teacher_id)
        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status,
            "student_id": l.student_id,
            "subscription_id": l.subscription_id
        } for l in lessons]

        return jsonify(lessons_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/subscription/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription_lessons(subscription_id):
    current_user_id = get_jwt_identity()

    try:
        lessons = repo_lessons.get_lessons_by_subscription(subscription_id)
        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status
        } for l in lessons]

        return jsonify(lessons_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_lessons():
    current_user_id = get_jwt_identity()
    try:
        user = repo_users.get_user_by_id(current_user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        user_type = 'teacher' if repo_roles.get_teacher_by_user_id(current_user_id) else 'student'

        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        lessons, total = repo_lessons.get_upcoming_lessons(
            user_id=current_user_id,
            user_type=user_type,
            page=page,
            per_page=per_page
        )

        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status,
            "student_id": l.student_id if user_type == 'teacher' else None,
            "teacher_id": l.teacher_id if user_type == 'student' else None,
            "subscription_id": l.subscription_id,
            "classroom_name": l.classroom.name if l.classroom else None,
            "branch_name": l.classroom.branch.address if l.classroom else None,
            "online_call_url": l.online_call_url if l.online_call_url else None,
            "student_full_name": l.student.user.full_name,
            "teacher_full_name": l.teacher.user.full_name,
            "discipline_name": l.discipline.name if l.discipline else None
        } for l in lessons]

        return jsonify({
            "data": lessons_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/past', methods=['GET'])
@jwt_required()
def get_past_lessons():
    current_user_id = get_jwt_identity()

    try:
        user = repo_users.get_user_by_id(current_user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        user_type = 'teacher' if repo_roles.get_teacher_by_user_id(current_user_id) else 'student'

        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        lessons, total = repo_lessons.get_past_lessons(
            user_id=current_user_id,
            user_type=user_type,
            page=page,
            per_page=per_page
        )

        lessons_data = [{
            "lesson_id": l.lesson_id,
            "lesson_date_time": l.lesson_date_time.isoformat(),
            "duration": l.duration,
            "status": l.status,
            "student_id": l.student_id if user_type == 'teacher' else None,
            "teacher_id": l.teacher_id if user_type == 'student' else None,
            "subscription_id": l.subscription_id,
            "classroom_name": l.classroom.name if l.classroom else None,
            "branch_name": l.classroom.branch.address if l.classroom else None,
            "online_call_url": l.online_call_url if l.online_call_url else None,
            "student_full_name": l.student.user.full_name,
            "teacher_full_name": l.teacher.user.full_name,
            "discipline_id": l.discipline_id,
            "discipline_name": l.discipline.name if l.discipline else None
        } for l in lessons]
        return jsonify({
            "data": lessons_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@lessons_bp.route('/cancel/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def cancel_lesson(lesson_id):
    current_user_id = get_jwt_identity()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        cancelled_lesson = repo_lessons.cancel_lesson(lesson_id)
        subscription_id = cancelled_lesson.subscription_id

        # Проверяем, что подписка существует
        if subscription_id:
            subscription = repo_subscriptions.get_subscription_by_id(subscription_id)

            if subscription:
                # Увеличиваем количество доступных занятий
                repo_subscriptions.update_subscription(
                    subscription_id=subscription_id,
                    total_lessons=subscription.total_lessons + 1
                )

                # Если подписка в архиве - выводим из архива
                if subscription.in_archive:
                    repo_subscriptions.update_subscription(
                        subscription_id=subscription_id,
                        in_archive=False
                    )

        return jsonify({
            "message": "Lesson cancelled successfully",
            "lesson_id": cancelled_lesson.lesson_id,
            "status": cancelled_lesson.status
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@lessons_bp.route('/complete/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def complete_lesson(lesson_id):
    current_user_id = get_jwt_identity()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        completed_lesson = repo_lessons.complete_lesson(lesson_id)

        return jsonify({
            "message": "Lesson completed successfully",
            "lesson_id": completed_lesson.lesson_id,
            "status": completed_lesson.status
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@lessons_bp.route('/missed/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def missed_lesson(lesson_id):
    current_user_id = get_jwt_identity()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        completed_lesson = repo_lessons.miss_lesson(lesson_id)

        return jsonify({
            "message": "Lesson missed successfully",
            "lesson_id": completed_lesson.lesson_id,
            "status": completed_lesson.status
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@lessons_bp.route('/delete/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
def delete_lesson(lesson_id):
    current_user_id = get_jwt_identity()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_lessons.delete_lesson(lesson_id):
            return jsonify({
                "message": "Lesson delete successfully"
            }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@lessons_bp.route('/save_delete/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
def save_delete_lesson(lesson_id):
    current_user_id = get_jwt_identity()

    try:
        lesson = repo_lessons.get_lesson_by_id(lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        if lesson.teacher_id != int(current_user_id) and not repo_roles.get_administrator_by_user_id(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        subscription_id = lesson.subscription_id
        subscription_on_delete_lesson = repo_subscriptions.get_subscription_by_id(subscription_id)

        if subscription_on_delete_lesson.in_archive:
            updated_subscription = repo_subscriptions.update_subscription(
                subscription_id=subscription_id,
                in_archive=False
            )

        if repo_lessons.delete_lesson(lesson_id):
            return jsonify({
                "message": "Lesson save delete successfully, set status in_archive to false"
            }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500