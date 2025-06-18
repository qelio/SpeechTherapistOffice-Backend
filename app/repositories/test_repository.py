from typing import List, Optional
from sqlalchemy import select, and_, delete, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Test, EducationExercise, TestExerciseAssociation, Teacher, Discipline
from datetime import datetime

class TestRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_tests(self) -> List[Test]:
        return self.session.query(Test).all()

    def get_test_by_id(self, test_id: int) -> Optional[Test]:
        return self.session.execute(
            select(Test)
            .where(Test.test_id == test_id)
        ).scalar_one_or_none()

    def get_tests_by_teacher(self, teacher_id: int) -> List[Test]:
        return self.session.execute(
            select(Test)
            .where(Test.teacher_id == teacher_id)
        ).scalars().all()

    def get_tests_by_discipline(self, discipline_id: int) -> List[Test]:
        return self.session.execute(
            select(Test)
            .where(Test.discipline_id == discipline_id)
        ).scalars().all()

    def get_exercises_for_test(self, test_id: int) -> List[EducationExercise]:
        return self.session.execute(
            select(EducationExercise)
            .join(TestExerciseAssociation, EducationExercise.exercise_id == TestExerciseAssociation.exercise_id)
            .where(TestExerciseAssociation.test_id == test_id)
        ).scalars().all()

    def create_test(
            self,
            name: str,
            complexity: str,
            discipline_id: int,
            teacher_id: int,
            description: Optional[str] = None
    ) -> Test:
        try:
            test = Test(
                name=name,
                description=description,
                complexity=complexity,
                discipline_id=discipline_id,
                teacher_id=teacher_id
            )
            self.session.add(test)
            self.session.commit()
            return test
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании теста: {str(e)}")

    def update_test(
            self,
            test_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            complexity: Optional[str] = None,
            discipline_id: Optional[int] = None
    ) -> Optional[Test]:
        test = self.get_test_by_id(test_id)
        if not test:
            return None

        try:
            if name is not None:
                test.name = name
            if description is not None:
                test.description = description
            if complexity is not None:
                test.complexity = complexity
            if discipline_id is not None:
                test.discipline_id = discipline_id

            self.session.commit()
            return test
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении теста: {str(e)}")

    def delete_test(self, test_id: int) -> bool:
        test = self.get_test_by_id(test_id)
        if test:
            self.session.execute(
                delete(TestExerciseAssociation)
                .where(TestExerciseAssociation.test_id == test_id)
            )
            self.session.delete(test)
            self.session.commit()
            return True
        return False

    def add_exercise_to_test(self, test_id: int, exercise_id: int) -> TestExerciseAssociation:
        try:
            association = TestExerciseAssociation(
                test_id=test_id,
                exercise_id=exercise_id,
                purpose_at=datetime.utcnow()
            )
            self.session.add(association)
            self.session.commit()
            return association
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при добавлении упражнения к тесту: {str(e)}")

    def remove_exercise_from_test(self, test_id: int, exercise_id: int) -> bool:
        association = self.session.execute(
            select(TestExerciseAssociation)
            .where(and_(
                TestExerciseAssociation.test_id == test_id,
                TestExerciseAssociation.exercise_id == exercise_id
            ))
        ).scalar_one_or_none()

        if association:
            self.session.delete(association)
            self.session.commit()
            return True
        return False

    def check_exercise_in_test(self, test_id: int, exercise_id: int) -> bool:
        association = self.session.execute(
            select(TestExerciseAssociation)
            .where(and_(
                TestExerciseAssociation.test_id == test_id,
                TestExerciseAssociation.exercise_id == exercise_id
            ))
        ).scalar_one_or_none()
        return association is not None

    def get_tests_with_exercise(self, exercise_id: int) -> List[Test]:
        return self.session.execute(
            select(Test)
            .join(TestExerciseAssociation, Test.test_id == TestExerciseAssociation.test_id)
            .where(TestExerciseAssociation.exercise_id == exercise_id)
        ).scalars().all()

    def get_paginated_tests(self, page: int = 1, per_page: int = 10) -> tuple[list[Test], dict]:
        if page < 1 or per_page < 1 or per_page > 100:
            raise ValueError("Invalid pagination parameters")

        total = self.session.execute(
            select(func.count()).select_from(Test)
        ).scalar_one()

        tests = self.session.execute(
            select(Test)
            .order_by(Test.test_id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).scalars().all()

        meta = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        }

        return tests, meta

    def get_exercises_count_by_test(self, test_id: int) -> int:
        return self.session.execute(
            select(func.count(TestExerciseAssociation.exercise_id))
            .where(TestExerciseAssociation.test_id == test_id)
        ).scalar_one()