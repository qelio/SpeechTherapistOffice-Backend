from typing import List, Optional
from sqlalchemy import select, and_, or_, delete, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models import ActiveTest, TestPackage, Test, Lesson, Student, Teacher, EducationExercise, User


class ActiveTestRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_active_tests(self) -> List[ActiveTest]:
        return self.session.query(ActiveTest).all()

    def get_active_test_by_id(self, active_id: int) -> Optional[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(ActiveTest.active_id == active_id)
        ).scalar_one_or_none()

    def get_active_tests_by_student(self, student_id: int) -> List[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(ActiveTest.student_id == student_id)
        ).scalars().all()

    def get_active_tests_by_teacher(self, teacher_id: int) -> List[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(ActiveTest.teacher_id == teacher_id)
        ).scalars().all()

    def get_active_tests_by_test(self, test_id: int) -> List[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(ActiveTest.test_id == test_id)
        ).scalars().all()

    def get_active_tests_by_lesson(self, lesson_id: int) -> List[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(ActiveTest.lesson_id == lesson_id)
        ).scalars().all()

    def create_active_test(
            self,
            test_id: int,
            student_id: int,
            teacher_id: int,
            status: str = 'active_not_sent',
            lesson_id: Optional[int] = None,
            time_start: Optional[datetime] = None,
            time_end: Optional[datetime] = None
    ) -> ActiveTest:
        try:
            active_test = ActiveTest(
                test_id=test_id,
                student_id=student_id,
                teacher_id=teacher_id,
                status=status,
                lesson_id=lesson_id,
                time_start=time_start,
                time_end=time_end
            )
            self.session.add(active_test)
            self.session.commit()
            return active_test
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error creating active test: {str(e)}")

    def update_active_test(
            self,
            active_id: int,
            status: Optional[str] = None,
            assessment: Optional[int] = None,
            time_start: Optional[datetime] = None,
            time_end: Optional[datetime] = None
    ) -> Optional[ActiveTest]:
        active_test = self.get_active_test_by_id(active_id)
        if not active_test:
            return None

        try:
            if status is not None:
                active_test.status = status
            if assessment is not None:
                active_test.assessment = assessment
            if time_start is not None:
                active_test.time_start = time_start
            if time_end is not None:
                active_test.time_end = time_end

            self.session.commit()
            return active_test
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error updating active test: {str(e)}")

    def delete_active_test(self, active_id: int) -> bool:
        active_test = self.get_active_test_by_id(active_id)
        if active_test:
            self.session.execute(
                delete(TestPackage)
                .where(TestPackage.active_id == active_id)
            )
            self.session.delete(active_test)
            self.session.commit()
            return True
        return False

    def start_test(self, active_id: int) -> Optional[ActiveTest]:
        active_test = self.get_active_test_by_id(active_id)
        if active_test:
            active_test.time_start = datetime.utcnow()
            self.session.commit()
            return active_test
        return None

    def complete_test(self, active_id: int, assessment: Optional[int] = None) -> Optional[ActiveTest]:
        active_test = self.get_active_test_by_id(active_id)
        if active_test:
            active_test.time_end = datetime.utcnow()
            active_test.status = 'active_sent'
            if assessment is not None:
                active_test.assessment = assessment
            self.session.commit()
            return active_test
        return None

    def get_packages_for_active_test(self, active_id: int) -> List[TestPackage]:
        return self.session.execute(
            select(TestPackage)
            .where(TestPackage.active_id == active_id)
        ).scalars().all()

    def add_package_to_active_test(
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
            raise ValueError(f"Error adding package to active test: {str(e)}")

    def update_package(
            self,
            package_id: int,
            status_verification: Optional[str] = None,
            student_answer: Optional[str] = None,
            file_url: Optional[str] = None,
            accumulated_score: Optional[int] = None,
            complete: bool = False
    ) -> Optional[TestPackage]:
        package = self.session.execute(
            select(TestPackage)
            .where(TestPackage.package_id == package_id)
        ).scalar_one_or_none()

        if not package:
            return None

        try:
            if status_verification is not None:
                package.status_verification = status_verification
            if student_answer is not None:
                package.student_answer = student_answer
            if file_url is not None:
                package.file_url = file_url
            if accumulated_score is not None:
                package.accumulated_score = accumulated_score
            if complete:
                package.exercise_end = datetime.utcnow()

            self.session.commit()
            return package
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error updating package: {str(e)}")

    def verify_package(self, package_id: int, score: int) -> Optional[TestPackage]:
        return self.update_package(
            package_id=package_id,
            status_verification='verified',
            accumulated_score=score
        )

    def get_completed_tests_by_student(self, student_id: int) -> List[ActiveTest]:
        return self.session.execute(
            select(ActiveTest)
            .where(and_(
                ActiveTest.student_id == student_id,
                ActiveTest.status == 'active_sent'
            ))
        ).scalars().all()

    def get_correct_answers_count(self, active_id: int) -> int:
        return self.session.execute(
            select(func.count(TestPackage.package_id))
            .join(EducationExercise, TestPackage.exercise_id == EducationExercise.exercise_id)
            .where(and_(
                TestPackage.active_id == active_id,
                TestPackage.student_answer == EducationExercise.right_answer
            ))
        ).scalar()

    def get_exercises_with_answers(self, active_id: int) -> List[dict]:
        packages = self.session.execute(
            select(TestPackage)
            .where(TestPackage.active_id == active_id)
            .join(EducationExercise, TestPackage.exercise_id == EducationExercise.exercise_id)
        ).scalars().all()

        return [{
            "exercise_id": p.exercise_id,
            "student_answer": p.student_answer,
            "is_correct": p.status_verification == 'verified' and p.accumulated_score > 0,
            "right_answer": p.exercise.right_answer if p.exercise else None,
            "score": p.accumulated_score
        } for p in packages]

    def get_teacher_student_tests(self, teacher_id: int) -> List[dict]:
        active_tests = self.session.execute(
            select(ActiveTest)
            .join(Test, ActiveTest.test_id == Test.test_id)
            .join(Student, ActiveTest.student_id == Student.user_id)
            .join(User, Student.user_id == User.user_id)
            .where(ActiveTest.teacher_id == teacher_id)
            .options(
                joinedload(ActiveTest.test),
                joinedload(ActiveTest.student).joinedload(Student.user),
                joinedload(ActiveTest.packages).joinedload(TestPackage.exercise)
            )
        ).unique().scalars().all()

        result = []
        for test in active_tests:
            exercises = []
            correct_answers = 0

            for package in test.packages:
                is_correct = package.student_answer == package.exercise.right_answer
                if is_correct:
                    correct_answers += 1

                exercises.append({
                    "exercise_id": package.exercise.exercise_id,
                    "name": package.exercise.name,
                    "description": package.exercise.description,
                    "student_answer": package.student_answer,
                    "right_answer": package.exercise.right_answer,
                    "score": package.accumulated_score or 0,
                    "max_score": package.exercise.max_score,
                    "is_correct": is_correct
                })

            result.append({
                "active_id": test.active_id,
                "test_name": test.test.name,
                "student_name": test.student.user.full_name,
                "discipline": test.test.discipline.name if test.test.discipline else None,
                "status": test.status,
                "time_start": test.time_start.isoformat() if test.time_start else None,
                "time_end": test.time_end.isoformat() if test.time_end else None,
                "total_exercises": len(exercises),
                "correct_answers": correct_answers,
                "exercises": exercises
            })

        return result