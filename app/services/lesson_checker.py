from flask import current_app
from datetime import datetime, timedelta
from app.repositories import LessonRepository, SubscriptionRepository
from app.db import db


class LessonChecker:
    def __init__(self, app):
        self.app = app

    def check_and_update_lessons(self):
        with self.app.app_context():
            repo = LessonRepository(db.session)
            repo_subscriptions = SubscriptionRepository(db.session)
            now = datetime.now()
            time_threshold = now - timedelta(minutes=5)

            lessons = repo.get_lessons_to_complete(time_threshold)

            for lesson in lessons:
                repo.complete_lesson(lesson.lesson_id)
                print(f"Урок {lesson.lesson_id} помечен как завершенный")

                subscription = lesson.subscription
                lessons_for_subscription = repo.get_lessons_by_subscription(lesson.subscription_id)
                lessons_counter = 0

                for lesson_subscription in lessons_for_subscription:
                    if lesson_subscription.status != 'scheduled':
                        lessons_counter += 1

                if subscription.total_lessons == lessons_counter:
                    repo_subscriptions.archive_subscription(subscription.subscription_id)
                    print(f"Абонемент {subscription.subscription_id} отправлен в архив")

            return len(lessons)