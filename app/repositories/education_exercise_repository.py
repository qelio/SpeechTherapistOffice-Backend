from datetime import datetime

from app.models import EducationExercise, EducationModule, Teacher, EducationClassifier
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

class EducationExerciseRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_exercises(self) -> List[EducationExercise]:
        return self.session.query(EducationExercise).all()

    def get_exercise_by_id(self, exercise_id: int) -> Optional[EducationExercise]:
        return self.session.execute(
            select(EducationExercise)
            .where(EducationExercise.exercise_id == exercise_id)
        ).scalar_one_or_none()

    def get_exercises_by_module(self, module_id: int) -> List[EducationExercise]:
        return self.session.execute(
            select(EducationExercise)
            .where(EducationExercise.module_id == module_id)
        ).scalars().all()

    def get_exercises_by_teacher(self, teacher_id: int) -> List[EducationExercise]:
        return self.session.execute(
            select(EducationExercise)
            .where(EducationExercise.teacher_id == teacher_id)
        ).scalars().all()

    def get_exercises_by_discipline(self, discipline_id: int) -> List[EducationExercise]:
        return self.session.execute(
            select(EducationExercise)
            .join(EducationModule, EducationExercise.module_id == EducationModule.module_id)
            .join(EducationClassifier, EducationModule.classifier_id == EducationClassifier.classifier_id)
            .where(EducationClassifier.discipline_id == discipline_id)
            .options(
                joinedload(EducationExercise.module),
                joinedload(EducationExercise.teacher)
                .joinedload(Teacher.user)
            )
        ).scalars().all()

    def create_exercise(
        self,
        name: str,
        description: str,
        verification_type: str,
        max_score: int,
        module_id: int,
        teacher_id: int,
        right_answer: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> EducationExercise:
        try:
            exercise = EducationExercise(
                name=name,
                description=description,
                verification_type=verification_type,
                right_answer=right_answer,
                max_score=max_score,
                created_at=created_at or datetime.utcnow(),
                module_id=module_id,
                teacher_id=teacher_id
            )
            self.session.add(exercise)
            self.session.commit()
            return exercise
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании упражнения: {str(e)}")

    def update_exercise(
        self,
        exercise_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        verification_type: Optional[str] = None,
        right_answer: Optional[str] = None,
        max_score: Optional[int] = None,
        module_id: Optional[int] = None,
        teacher_id: Optional[int] = None
    ) -> Optional[EducationExercise]:
        exercise = self.get_exercise_by_id(exercise_id)
        if not exercise:
            return None

        try:
            if name is not None:
                exercise.name = name
            if description is not None:
                exercise.description = description
            if verification_type is not None:
                exercise.verification_type = verification_type
            if right_answer is not None:
                exercise.right_answer = right_answer
            if max_score is not None:
                exercise.max_score = max_score
            if module_id is not None:
                exercise.module_id = module_id
            if teacher_id is not None:
                exercise.teacher_id = teacher_id

            self.session.commit()
            return exercise
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении упражнения: {str(e)}")

    def delete_exercise(self, exercise_id: int) -> bool:
        exercise = self.get_exercise_by_id(exercise_id)
        if exercise:
            self.session.delete(exercise)
            self.session.commit()
            return True
        return False

    def get_filtered_exercises(
            self,
            page: int = 1,
            per_page: int = 10,
            discipline_id: Optional[int] = None,
            classifier_id: Optional[int] = None,
            module_id: Optional[int] = None,
            teacher_id: Optional[int] = None
    ) -> Tuple[List[EducationExercise], int]:
        query = select(EducationExercise)

        if module_id:
            query = query.where(EducationExercise.module_id == module_id)

        if classifier_id:
            query = query.join(
                EducationModule,
                EducationExercise.module_id == EducationModule.module_id
            ).where(EducationModule.classifier_id == classifier_id)

        if discipline_id:
            query = query.join(
                EducationModule,
                EducationExercise.module_id == EducationModule.module_id
            ).join(
                EducationClassifier,
                EducationModule.classifier_id == EducationClassifier.classifier_id
            ).where(EducationClassifier.discipline_id == discipline_id)

        if teacher_id:
            query = query.where(EducationExercise.teacher_id == teacher_id)

        total_count = self.session.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar()

        exercises = self.session.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        ).scalars().all()

        return exercises, total_count