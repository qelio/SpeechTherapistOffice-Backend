from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Discipline, Teacher, TeacherDisciplineAssociation, Administrator
from datetime import datetime

class DisciplineRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_disciplines(self) -> List[Discipline]:
        return self.session.query(Discipline).all()

    def get_discipline_by_id(self, discipline_id: int) -> Optional[Discipline]:
        return self.session.execute(
            select(Discipline)
            .where(Discipline.discipline_id == discipline_id)
        ).scalar_one_or_none()

    def get_disciplines_by_administrator(self, administrator_id: int) -> List[Discipline]:
        return self.session.execute(
            select(Discipline)
            .where(Discipline.administrator_id == administrator_id)
        ).scalars().all()

    def get_disciplines_for_teacher(self, teacher_id: int) -> List[Discipline]:
        return self.session.execute(
            select(Discipline)
            .join(TeacherDisciplineAssociation, Discipline.discipline_id == TeacherDisciplineAssociation.discipline_id)
            .where(TeacherDisciplineAssociation.teacher_id == teacher_id)
        ).scalars().all()

    def get_teachers_for_discipline(self, discipline_id: int) -> List[Teacher]:
        return self.session.execute(
            select(Teacher)
            .join(TeacherDisciplineAssociation, Teacher.user_id == TeacherDisciplineAssociation.teacher_id)
            .where(TeacherDisciplineAssociation.discipline_id == discipline_id)
        ).scalars().all()

    def create_discipline(
            self,
            name: str,
            description: str,
            administrator_id: int
    ) -> Discipline:
        try:
            discipline = Discipline(
                name=name,
                description=description,
                administrator_id=administrator_id,
                created_at=datetime.utcnow()
            )
            self.session.add(discipline)
            self.session.commit()
            return discipline
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании дисциплины: {str(e)}")

    def update_discipline(
            self,
            discipline_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            administrator_id: Optional[int] = None
    ) -> Optional[Discipline]:
        discipline = self.get_discipline_by_id(discipline_id)
        if not discipline:
            return None

        try:
            if name is not None:
                discipline.name = name
            if description is not None:
                discipline.description = description
            if administrator_id is not None:
                discipline.administrator_id = administrator_id

            self.session.commit()
            return discipline
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении дисциплины: {str(e)}")

    def delete_discipline(self, discipline_id: int) -> bool:
        discipline = self.get_discipline_by_id(discipline_id)
        if discipline:
            self.session.delete(discipline)
            self.session.commit()
            return True
        return False

    def add_teacher_to_discipline(self, teacher_id: int, discipline_id: int) -> TeacherDisciplineAssociation:
        try:
            association = TeacherDisciplineAssociation(
                teacher_id=teacher_id,
                discipline_id=discipline_id
            )
            self.session.add(association)
            self.session.commit()
            return association
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при добавлении преподавателя к дисциплине: {str(e)}")

    def remove_teacher_from_discipline(self, teacher_id: int, discipline_id: int) -> bool:
        association = self.session.execute(
            select(TeacherDisciplineAssociation)
            .where(and_(
                TeacherDisciplineAssociation.teacher_id == teacher_id,
                TeacherDisciplineAssociation.discipline_id == discipline_id
            ))
        ).scalar_one_or_none()

        if association:
            self.session.delete(association)
            self.session.commit()
            return True
        return False

    def check_teacher_discipline_association(self, teacher_id: int, discipline_id: int) -> bool:
        association = self.session.execute(
            select(TeacherDisciplineAssociation)
            .where(and_(
                TeacherDisciplineAssociation.teacher_id == teacher_id,
                TeacherDisciplineAssociation.discipline_id == discipline_id
            ))
        ).scalar_one_or_none()
        return association is not None