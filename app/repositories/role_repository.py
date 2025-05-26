from typing import Optional, Type
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Student, Teacher, Parent, Administrator
from sqlalchemy.exc import IntegrityError

class RoleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_student_by_user_id(self, user_id: int) -> Optional[Student]:
        return self.session.get(Student, user_id)

    def get_teacher_by_user_id(self, user_id: int) -> Optional[Teacher]:
        return self.session.get(Teacher, user_id)

    def get_parent_by_user_id(self, user_id: int) -> Optional[Parent]:
        return self.session.get(Parent, user_id)

    def get_administrator_by_user_id(self, user_id: int) -> Optional[Administrator]:
        return self.session.get(Administrator, user_id)