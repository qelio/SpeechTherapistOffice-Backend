from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Lesson, Subscription, Student, Teacher


class LessonRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_lessons(self) -> List[Lesson]:
        return self.session.query(Lesson).all()

    def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        return self.session.execute(
            select(Lesson)
            .where(Lesson.lesson_id == lesson_id)
        ).scalar_one_or_none()

    def get_lessons_for_student(self, student_id: int) -> List[Lesson]:
        return self.session.execute(
            select(Lesson)
            .where(Lesson.student_id == student_id)
            .order_by(Lesson.lesson_date_time)
        ).scalars().all()

    def get_lessons_for_teacher(self, teacher_id: int) -> List[Lesson]:
        return self.session.execute(
            select(Lesson)
            .where(Lesson.teacher_id == teacher_id)
            .order_by(Lesson.lesson_date_time)
        ).scalars().all()

    def get_lessons_by_subscription(self, subscription_id: int) -> List[Lesson]:
        return self.session.execute(
            select(Lesson)
            .where(Lesson.subscription_id == subscription_id)
            .order_by(Lesson.lesson_date_time)
        ).scalars().all()

    def get_upcoming_lessons(self, user_id: int, user_type: str, limit: int = 10) -> List[Lesson]:
        now = datetime.now()
        if user_type == 'student':
            condition = Lesson.student_id == user_id
        elif user_type == 'teacher':
            condition = Lesson.teacher_id == user_id
        else:
            raise ValueError("Invalid user type. Use 'student' or 'teacher'")

        return self.session.execute(
            select(Lesson)
            .where(and_(
                condition,
                Lesson.lesson_date_time >= now,
                Lesson.status == 'scheduled'
            ))
            .order_by(Lesson.lesson_date_time)
            .limit(limit)
        ).scalars().all()

    def create_lesson(
            self,
            lesson_date_time: datetime,
            duration: int,
            status: str,
            teacher_id: int,
            student_id: int,
            subscription_id: Optional[int] = None,
            online_call_url: Optional[str] = None
    ) -> Lesson:
        try:
            lesson = Lesson(
                lesson_date_time=lesson_date_time,
                duration=duration,
                status=status,
                teacher_id=teacher_id,
                student_id=student_id,
                subscription_id=subscription_id,
                online_call_url=online_call_url,
                created_at=datetime.now()
            )
            self.session.add(lesson)
            self.session.commit()
            return lesson
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании урока: {str(e)}")

    def update_lesson(
            self,
            lesson_id: int,
            lesson_date_time: Optional[datetime] = None,
            duration: Optional[int] = None,
            status: Optional[str] = None,
            online_call_url: Optional[str] = None,
            subscription_id: Optional[int] = None
    ) -> Optional[Lesson]:
        lesson = self.get_lesson_by_id(lesson_id)
        if not lesson:
            return None

        try:
            if lesson_date_time is not None:
                lesson.lesson_date_time = lesson_date_time
            if duration is not None:
                lesson.duration = duration
            if status is not None:
                lesson.status = status
            if online_call_url is not None:
                lesson.online_call_url = online_call_url
            if subscription_id is not None:
                lesson.subscription_id = subscription_id

            self.session.commit()
            return lesson
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении урока: {str(e)}")

    def delete_lesson(self, lesson_id: int) -> bool:
        lesson = self.get_lesson_by_id(lesson_id)
        if lesson:
            self.session.delete(lesson)
            self.session.commit()
            return True
        return False

    def cancel_lesson(self, lesson_id: int) -> Optional[Lesson]:
        return self.update_lesson(
            lesson_id,
            status='cancelled_in_time'
        )

    def complete_lesson(self, lesson_id: int) -> Optional[Lesson]:
        return self.update_lesson(
            lesson_id,
            status='completed'
        )