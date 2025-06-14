from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Classroom, Branch, Administrator
from datetime import datetime


class ClassroomRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_classrooms(self) -> List[Classroom]:
        return self.session.query(Classroom).all()

    def get_classroom_by_id(self, classroom_id: int) -> Optional[Classroom]:
        return self.session.execute(
            select(Classroom)
            .where(Classroom.classroom_id == classroom_id)
        ).scalar_one_or_none()

    def get_classrooms_by_branch(self, branch_id: int) -> List[Classroom]:
        return self.session.execute(
            select(Classroom)
            .where(Classroom.branch_id == branch_id)
        ).scalars().all()

    def get_classrooms_by_administrator(self, administrator_id: int) -> List[Classroom]:
        return self.session.execute(
            select(Classroom)
            .where(Classroom.administrator_id == administrator_id)
        ).scalars().all()

    def create_classroom(
        self,
        classroom_id: int,
        name: str,
        branch_id: int,
        administrator_id: int,
        description: Optional[str] = None
    ) -> Classroom:
        try:
            classroom = Classroom(
                classroom_id=classroom_id,
                name=name,
                description=description,
                branch_id=branch_id,
                administrator_id=administrator_id,
                updated_at=datetime.utcnow()
            )
            self.session.add(classroom)
            self.session.commit()
            return classroom
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании аудитории: {str(e)}")

    def update_classroom(
        self,
        classroom_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        branch_id: Optional[int] = None,
        administrator_id: Optional[int] = None
    ) -> Optional[Classroom]:
        classroom = self.get_classroom_by_id(classroom_id)
        if not classroom:
            return None

        try:
            if name is not None:
                classroom.name = name
            if description is not None:
                classroom.description = description
            if branch_id is not None:
                classroom.branch_id = branch_id
            if administrator_id is not None:
                classroom.administrator_id = administrator_id

            classroom.updated_at = datetime.utcnow()
            self.session.commit()
            return classroom
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении аудитории: {str(e)}")

    def delete_classroom(self, classroom_id: int) -> bool:
        classroom = self.get_classroom_by_id(classroom_id)
        if classroom:
            self.session.delete(classroom)
            self.session.commit()
            return True
        return False