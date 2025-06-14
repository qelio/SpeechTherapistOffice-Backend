from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.repositories import RoleRepository, SubscriptionRepository, LessonRepository
from app.repositories.association_teacher_student_repository import AssociationTeacherStudentRepository
from app.repositories.user_repository import UserRepository
from app.db import db
from datetime import datetime

subscriptions_bp = Blueprint('subscriptions', __name__)
repo_subscriptions = SubscriptionRepository(db.session)
repo_lessons = LessonRepository(db.session)
repo_roles = RoleRepository(db.session)


@subscriptions_bp.route('/create', methods=['POST'])
@jwt_required()
def create_subscription():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = {
        'total_lessons', 'start_date',
        'end_date', 'student_id'
    }

    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)
        if not teacher:
            return jsonify({"message": "Only teachers can create subscriptions"}), 403

        subscription = repo_subscriptions.create_subscription(
            total_lessons=data['total_lessons'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            student_id=data['student_id'],
            teacher_id=current_user_id
        )

        return jsonify({
            "message": "Subscription created successfully",
            "subscription_id": subscription.subscription_id
        }), 201

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id):
    current_user_id = get_jwt_identity()

    try:
        subscription = repo_subscriptions.get_subscription_by_id(subscription_id)
        if not subscription:
            return jsonify({"message": "Subscription not found"}), 404

        if (subscription.student_id != current_user_id and
                subscription.teacher_id != current_user_id):
            return jsonify({"message": "Access denied"}), 403

        subscription_data = {
            "subscription_id": subscription.subscription_id,
            "total_lessons": subscription.total_lessons,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "created_at": subscription.created_at.isoformat(),
            "in_archive": subscription.in_archive,
            "student_id": subscription.student_id,
            "teacher_id": subscription.teacher_id
        }

        return jsonify(subscription_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_subscriptions(student_id):
    current_user_id = get_jwt_identity()

    try:
        student = repo_roles.get_student_by_user_id(student_id)
        teacher = repo_roles.get_teacher_by_user_id(current_user_id)

        if student_id != current_user_id and not teacher:
            return jsonify({"message": "Access denied"}), 403

        subscriptions = repo_subscriptions.get_subscriptions_for_student(student_id)

        subscriptions_data = [{
            "subscription_id": sub.subscription_id,
            "total_lessons": sub.total_lessons,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "teacher_id": sub.teacher_id,
            "in_archive": sub.in_archive
        } for sub in subscriptions]

        return jsonify(subscriptions_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/teacher', methods=['GET'])
@jwt_required()
def get_teacher_subscriptions():
    current_user_id = get_jwt_identity()

    try:
        subscriptions = repo_subscriptions.get_subscriptions_for_teacher(current_user_id)

        subscriptions_data = []
        for sub in subscriptions:
            lessons = repo_lessons.get_lessons_by_subscription(sub.subscription_id)

            lessons_data = [{
                "lesson_id": lesson.lesson_id,
                "lesson_date_time": lesson.lesson_date_time.isoformat(),
                "duration": lesson.duration,
                "status": lesson.status,
                "online_call_url": lesson.online_call_url
            } for lesson in lessons]

            subscription_data = {
                "subscription_id": sub.subscription_id,
                "total_lessons": sub.total_lessons,
                "start_date": sub.start_date.isoformat(),
                "end_date": sub.end_date.isoformat(),
                "student_id": sub.student_id,
                "student_full_name": sub.student.user.full_name,
                "teacher_id": sub.teacher_id,
                "teacher_full_name": sub.teacher.user.full_name,
                "in_archive": sub.in_archive,
                "lessons": lessons_data
            }
            subscriptions_data.append(subscription_data)

        return jsonify(subscriptions_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/update/<int:subscription_id>', methods=['PUT'])
@jwt_required()
def update_subscription(subscription_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        subscription = repo_subscriptions.get_subscription_by_id(subscription_id)
        if not subscription:
            return jsonify({"message": "Subscription not found"}), 404

        if subscription.teacher_id != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        allowed_fields = {
            'total_lessons', 'end_date', 'in_archive'
        }

        update_data = {
            k: datetime.fromisoformat(v) if k == 'end_date' else v
            for k, v in data.items()
            if k in allowed_fields
        }

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        updated_subscription = repo_subscriptions.update_subscription(
            subscription_id, **update_data
        )

        if not updated_subscription:
            return jsonify({"message": "Failed to update subscription"}), 400

        return jsonify({
            "message": "Subscription updated successfully",
            "subscription_id": updated_subscription.subscription_id,
            "updated_fields": list(update_data.keys())
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/archive/<int:subscription_id>', methods=['PUT'])
@jwt_required()
def archive_subscription(subscription_id):
    current_user_id = get_jwt_identity()

    try:
        subscription = repo_subscriptions.get_subscription_by_id(subscription_id)
        if not subscription:
            return jsonify({"message": "Subscription not found"}), 404

        if subscription.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        archived_subscription = repo_subscriptions.archive_subscription(subscription_id)

        if not archived_subscription:
            return jsonify({"message": "Failed to archive subscription"}), 400

        return jsonify({
            "message": "Subscription archived successfully",
            "subscription_id": archived_subscription.subscription_id
        }), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@subscriptions_bp.route('/delete/<int:subscription_id>', methods=['DELETE'])
@jwt_required()
def delete_subscription(subscription_id):
    current_user_id = get_jwt_identity()

    try:
        subscription = repo_subscriptions.get_subscription_by_id(subscription_id)
        if not subscription:
            return jsonify({"message": "Subscription not found"}), 404
        if subscription.teacher_id != int(current_user_id):
            return jsonify({"message": "Access denied"}), 403

        if repo_subscriptions.delete_subscription(subscription_id):
            return jsonify({"message": "Subscription delete successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete subscription"}), 400

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscriptions_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_subscriptions():
    current_user_id = get_jwt_identity()
    student_id = request.args.get('student_id')
    teacher_id = request.args.get('teacher_id')

    try:
        if student_id:
            student_id = int(student_id)
            student = repo_roles.get_student_by_user_id(student_id)

            teacher = repo_roles.get_teacher_by_user_id(current_user_id)
            if student_id != current_user_id and not teacher:
                return jsonify({"message": "Access denied"}), 403

        if teacher_id and int(teacher_id) != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        subscriptions = repo_subscriptions.get_active_subscriptions(
            student_id=student_id,
            teacher_id=teacher_id or current_user_id
        )

        subscriptions_data = [{
            "subscription_id": sub.subscription_id,
            "total_lessons": sub.total_lessons,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "student_id": sub.student_id,
            "teacher_id": sub.teacher_id
        } for sub in subscriptions]

        return jsonify(subscriptions_data), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500