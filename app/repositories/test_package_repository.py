from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models import TestPackage, ActiveTest, EducationExercise

class TestPackageRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_package_by_id(self, package_id: int) -> Optional[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .where(TestPackage.package_id == package_id)
            .options(
                joinedload(TestPackage.active_test),
                joinedload(TestPackage.exercise)
            )
        ).unique().scalar_one_or_none()

    def get_packages_by_active_test(self, active_id: int) -> List[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .where(TestPackage.active_id == active_id)
            .options(joinedload(TestPackage.exercise))
        ).scalars().all()

    def get_packages_by_exercise(self, exercise_id: int) -> List[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .where(TestPackage.exercise_id == exercise_id)
            .options(joinedload(TestPackage.active_test))
        ).scalars().all()

    def get_student_packages(self, student_id: int) -> List[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .join(ActiveTest)
            .where(ActiveTest.student_id == student_id)
            .options(
                joinedload(TestPackage.active_test),
                joinedload(TestPackage.exercise)
            )
        ).scalars().all()

    def create_package(
        self,
        active_id: int,
        exercise_id: int,
        student_answer: Optional[str] = None,
        file_url: Optional[str] = None
    ) -> TestPackage:
        try:
            package = TestPackage(
                active_id=active_id,
                exercise_id=exercise_id,
                student_answer=student_answer,
                file_url=file_url,
                status_verification='not_verified',
                exercise_start=datetime.utcnow()
            )
            self.session.add(package)
            self.session.commit()
            return package
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error creating test package: {str(e)}")

    def update_package(
        self,
        package_id: int,
        student_answer: Optional[str] = None,
        file_url: Optional[str] = None,
        status_verification: Optional[str] = None,
        accumulated_score: Optional[int] = None,
        complete: bool = False
    ) -> Optional[TestPackage]:
        package = self.get_package_by_id(package_id)
        if not package:
            return None

        try:
            if student_answer is not None:
                package.student_answer = student_answer
            if file_url is not None:
                package.file_url = file_url
            if status_verification is not None:
                package.status_verification = status_verification
            if accumulated_score is not None:
                package.accumulated_score = accumulated_score
            if complete and not package.exercise_end:
                package.exercise_end = datetime.utcnow()

            self.session.commit()
            return package
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error updating package: {str(e)}")

    def submit_package(
        self,
        package_id: int,
        student_answer: Optional[str] = None,
        file_url: Optional[str] = None
    ) -> Optional[TestPackage]:
        return self.update_package(
            package_id=package_id,
            student_answer=student_answer,
            file_url=file_url,
            status_verification='not_verified',
            complete=True
        )

    def verify_package(
        self,
        package_id: int,
        score: int,
        status: str = 'verified'
    ) -> Optional[TestPackage]:
        package = self.get_package_by_id(package_id)
        if not package:
            return None

        if score > package.exercise.max_score:
            raise ValueError("Score cannot exceed exercise max score")

        return self.update_package(
            package_id=package_id,
            status_verification=status,
            accumulated_score=score
        )

    def delete_package(self, package_id: int) -> bool:
        package = self.get_package_by_id(package_id)
        if package:
            self.session.delete(package)
            self.session.commit()
            return True
        return False

    def get_package_stats(self, active_id: int) -> Dict[str, Any]:
        result = self.session.execute(
            select(
                func.count(TestPackage.package_id).label("total"),
                func.sum(TestPackage.accumulated_score).label("total_score"),
                func.avg(TestPackage.accumulated_score).label("average_score"),
                func.count(
                    case((TestPackage.status_verification == 'verified', 1))
                ).label("verified_count")
            )
            .where(TestPackage.active_id == active_id)
        ).one()

        return {
            "total_packages": result.total or 0,
            "total_score": result.total_score or 0,
            "average_score": round(result.average_score or 0, 2),
            "verified_count": result.verified_count or 0
        }

    def get_unverified_packages(self, teacher_id: int) -> List[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .join(ActiveTest)
            .where(and_(
                ActiveTest.teacher_id == teacher_id,
                TestPackage.status_verification == 'not_verified',
                TestPackage.exercise_end.is_not(None)
            ))
            .options(
                joinedload(TestPackage.active_test),
                joinedload(TestPackage.exercise)
            )
        ).scalars().all()