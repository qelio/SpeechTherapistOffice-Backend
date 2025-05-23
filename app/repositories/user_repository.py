from typing import Type

from app.models import User
from sqlalchemy.orm import Session

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self) -> list[Type[User]]:
        return self.session.query(User).all()