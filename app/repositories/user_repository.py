from typing import Optional, Type
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Student, Teacher, Parent, Administrator
from sqlalchemy.exc import IntegrityError

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self) -> list[Type[User]]:
        return self.session.query(User).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def create_user_with_role(self, user_data: dict) -> User:

        existing_user = self.get_user_by_email(user_data['email'])
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")


        try:
            user = User(
                full_name=user_data['fullName'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                birthday=user_data['birthDate'],
                gender=user_data['selectedGender'],
                city=user_data.get('city', ''),
                phone_number=user_data.get('phone', ''),
                profile_picture_url=user_data.get('profile_picture_url'),
                unique_code=user_data.get('unique_code', '')
            )

            self.session.add(user)
            self.session.flush()

            role = user_data.get('selectedRole', 'student').lower()

            if role == 'student':
                student = Student(
                    user_id=user.user_id,
                    class_number=user_data.get('class_number'),
                    school_name=user_data.get('school')
                )
                self.session.add(student)
            elif role == 'teacher':
                # TODO: исправить названия полей для учителя
                teacher = Teacher(
                    user_id=user.user_id,
                    experience=user_data.get('experience', 0),
                    main_work=user_data.get('main_work', '')
                )
                self.session.add(teacher)
            elif role == 'parent':
                parent = Parent(
                    user_id=user.user_id,
                    work_name=user_data.get('work'),
                    work_phone=user_data.get('workPhone')
                )
                self.session.add(parent)
            elif role == 'administrator':
                # TODO: исправить названия полей для администратора
                admin = Administrator(
                    Users_user_id=user.user_id,
                    access_level=user_data.get('access_level', 'logs')
                )
                self.session.add(admin)

            self.session.commit()
            return user


        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании пользователя: {str(e)}")

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        # TODO: исправить временную заглушку на проверку хэша
        if user and check_password_hash(user.password_hash, password):
            return user

        # if user and user.password_hash == password:
        #     return user
        return None

    def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in update_data.items():
                if key == 'password':
                    setattr(user, 'password_hash', generate_password_hash(value))
                else:
                    setattr(user, key, value)
            self.session.commit()
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False