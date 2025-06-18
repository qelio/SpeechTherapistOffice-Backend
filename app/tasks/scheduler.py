from apscheduler.schedulers.background import BackgroundScheduler
from app.services.lesson_checker import LessonChecker

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    checker = LessonChecker(app)

    scheduler.add_job(
        checker.check_and_update_lessons,
        'interval',
        minutes=1,
        id='lesson_status_check'
    )

    scheduler.start()