from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Branch, Administrator
from datetime import datetime, time


class BranchRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_branches(self) -> List[Branch]:
        return self.session.query(Branch).all()

    def get_branch_by_id(self, branch_id: int) -> Optional[Branch]:
        return self.session.execute(
            select(Branch)
            .where(Branch.branch_id == branch_id)
        ).scalar_one_or_none()

    def get_branches_by_administrator(self, administrator_id: int) -> List[Branch]:
        return self.session.execute(
            select(Branch)
            .where(Branch.administrator_id == administrator_id)
        ).scalars().all()

    def create_branch(
        self,
        address: Optional[str],
        working_start: time,
        working_end: time,
        description: Optional[str],
        photo_url: Optional[str],
        administrator_id: int
    ) -> Branch:
        try:
            branch = Branch(
                address=address,
                working_start=working_start,
                working_end=working_end,
                description=description,
                photo_url=photo_url,
                administrator_id=administrator_id,
                updated_at=datetime.utcnow()
            )
            self.session.add(branch)
            self.session.commit()
            return branch
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании филиала: {str(e)}")

    def update_branch(
        self,
        branch_id: int,
        address: Optional[str] = None,
        working_start: Optional[time] = None,
        working_end: Optional[time] = None,
        description: Optional[str] = None,
        photo_url: Optional[str] = None,
        administrator_id: Optional[int] = None
    ) -> Optional[Branch]:
        branch = self.get_branch_by_id(branch_id)
        if not branch:
            return None

        try:
            if address is not None:
                branch.address = address
            if working_start is not None:
                branch.working_start = working_start
            if working_end is not None:
                branch.working_end = working_end
            if description is not None:
                branch.description = description
            if photo_url is not None:
                branch.photo_url = photo_url
            if administrator_id is not None:
                branch.administrator_id = administrator_id

            branch.updated_at = datetime.utcnow()
            self.session.commit()
            return branch
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении филиала: {str(e)}")

    def delete_branch(self, branch_id: int) -> bool:
        branch = self.get_branch_by_id(branch_id)
        if branch:
            self.session.delete(branch)
            self.session.commit()
            return True
        return False