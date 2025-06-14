from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Subscription, Student, Teacher
from datetime import datetime, date


class SubscriptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_subscriptions(self) -> List[Subscription]:
        return self.session.query(Subscription).all()

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        return self.session.execute(
            select(Subscription)
            .where(Subscription.subscription_id == subscription_id)
        ).scalar_one_or_none()

    def get_subscriptions_for_student(self, student_id: int) -> List[Subscription]:
        return self.session.execute(
            select(Subscription)
            .where(Subscription.student_id == student_id)
        ).scalars().all()

    def get_subscriptions_for_teacher(self, teacher_id: int) -> List[Subscription]:
        return self.session.execute(
            select(Subscription)
            .where(Subscription.teacher_id == teacher_id)
        ).scalars().all()

    def get_active_subscriptions(self, student_id: int, teacher_id: int) -> List[Subscription]:
        return self.session.execute(
            select(Subscription)
            .where(and_(
                Subscription.student_id == student_id,
                Subscription.teacher_id == teacher_id,
                Subscription.in_archive == False
            ))
        ).scalars().all()

    def create_subscription(
            self,
            total_lessons: int,
            start_date: date,
            end_date: date,
            student_id: int,
            teacher_id: int,
            in_archive: bool = False
    ) -> Subscription:
        try:
            subscription = Subscription(
                total_lessons=total_lessons,
                start_date=start_date,
                end_date=end_date,
                student_id=student_id,
                teacher_id=teacher_id,
                in_archive=in_archive,
                created_at=datetime.utcnow()
            )
            self.session.add(subscription)
            self.session.commit()
            return subscription
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании подписки: {str(e)}")

    def update_subscription(
            self,
            subscription_id: int,
            total_lessons: Optional[int] = None,
            end_date: Optional[date] = None,
            in_archive: Optional[bool] = None
    ) -> Optional[Subscription]:
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            return None

        try:
            if total_lessons is not None:
                subscription.total_lessons = total_lessons
            if end_date is not None:
                subscription.end_date = end_date
            if in_archive is not None:
                subscription.in_archive = in_archive

            self.session.commit()
            return subscription
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении подписки: {str(e)}")

    def delete_subscription(self, subscription_id: int) -> bool:
        subscription = self.get_subscription_by_id(subscription_id)
        if subscription:
            self.session.delete(subscription)
            self.session.commit()
            return True
        return False

    def archive_subscription(self, subscription_id: int) -> Optional[Subscription]:
        return self.update_subscription(subscription_id, in_archive=True)