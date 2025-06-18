from datetime import datetime

from app.models import EducationModule, EducationClassifier, Teacher
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

class EducationModuleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_modules(self) -> List[EducationModule]:
        return self.session.query(EducationModule).all()

    def get_module_by_id(self, module_id: int) -> Optional[EducationModule]:
        return self.session.execute(
            select(EducationModule)
            .where(EducationModule.module_id == module_id)
        ).scalar_one_or_none()

    def get_modules_by_classifier(self, classifier_id: int) -> List[EducationModule]:
        return self.session.execute(
            select(EducationModule)
            .where(EducationModule.classifier_id == classifier_id)
        ).scalars().all()

    def get_modules_by_teacher(self, teacher_id: int) -> List[EducationModule]:
        return self.session.execute(
            select(EducationModule)
            .where(EducationModule.teacher_id == teacher_id)
        ).scalars().all()

    def create_module(
        self,
        description: str,
        classifier_id: int,
        teacher_id: int,
        preview_url: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> EducationModule:
        try:
            module = EducationModule(
                description=description,
                preview_url=preview_url,
                created_at=created_at or datetime.utcnow(),
                classifier_id=classifier_id,
                teacher_id=teacher_id
            )
            self.session.add(module)
            self.session.commit()
            return module
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании модуля: {str(e)}")

    def update_module(
        self,
        module_id: int,
        description: Optional[str] = None,
        preview_url: Optional[str] = None,
        classifier_id: Optional[int] = None,
        teacher_id: Optional[int] = None
    ) -> Optional[EducationModule]:
        module = self.get_module_by_id(module_id)
        if not module:
            return None

        try:
            if description is not None:
                module.description = description
            if preview_url is not None:
                module.preview_url = preview_url
            if classifier_id is not None:
                module.classifier_id = classifier_id
            if teacher_id is not None:
                module.teacher_id = teacher_id

            self.session.commit()
            return module
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении модуля: {str(e)}")

    def delete_module(self, module_id: int) -> bool:
        module = self.get_module_by_id(module_id)
        if module:
            self.session.delete(module)
            self.session.commit()
            return True
        return False