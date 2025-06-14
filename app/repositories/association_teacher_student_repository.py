from typing import List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import StudentTeacherAssociation, Student, Teacher

class AssociationTeacherStudentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_associations(self) -> List[StudentTeacherAssociation]:
        return self.session.query(StudentTeacherAssociation).all()

    def get_association(self, student_id: int, teacher_id: int) -> Optional[StudentTeacherAssociation]:
        return self.session.execute(
            select(StudentTeacherAssociation)
            .where(and_(
                StudentTeacherAssociation.student_user_id == student_id,
                StudentTeacherAssociation.teacher_user_id == teacher_id
            ))
        ).scalar_one_or_none()

    def get_teachers_for_student(self, student_id: int) -> List[Teacher]:
        return self.session.execute(
            select(Teacher)
            .join(StudentTeacherAssociation, Teacher.user_id == StudentTeacherAssociation.teacher_user_id)
            .where(StudentTeacherAssociation.student_user_id == student_id)
        ).scalars().all()

    def get_students_for_teacher(self, teacher_id: int) -> List[Student]:
        return self.session.execute(
            select(Student)
            .join(StudentTeacherAssociation, Student.user_id == StudentTeacherAssociation.student_user_id)
            .where(StudentTeacherAssociation.teacher_user_id == teacher_id)
        ).scalars().all()

    def create_association(self, student_id: int, teacher_id: int) -> StudentTeacherAssociation:
        existing = self.get_association(student_id, teacher_id)
        if existing:
            raise ValueError("Такая связь уже существует")

        try:
            association = StudentTeacherAssociation(
                student_user_id=student_id,
                teacher_user_id=teacher_id
            )
            self.session.add(association)
            self.session.commit()
            return association
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании связи: {str(e)}")

    def delete_association(self, student_id: int, teacher_id: int) -> bool:
        association = self.get_association(student_id, teacher_id)
        if association:
            self.session.delete(association)
            self.session.commit()
            return True
        return False

    def bulk_create_associations(self, student_ids: List[int], teacher_ids: List[int]) -> List[Tuple[int, int]]:
        created = []
        try:
            for student_id in student_ids:
                for teacher_id in teacher_ids:
                    if not self.get_association(student_id, teacher_id):
                        association = StudentTeacherAssociation(
                            student_user_id=student_id,
                            teacher_user_id=teacher_id
                        )
                        self.session.add(association)
                        created.append((student_id, teacher_id))
            self.session.commit()
            return created
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при массовом создании связей: {str(e)}")