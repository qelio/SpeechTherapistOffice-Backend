from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import EducationClassifier, Administrator, Discipline
from datetime import datetime


class EducationClassifierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_classifiers(self) -> List[EducationClassifier]:
        return self.session.query(EducationClassifier).all()

    def get_classifier_by_id(self, classifier_id: int) -> Optional[EducationClassifier]:
        return self.session.execute(
            select(EducationClassifier)
            .where(EducationClassifier.classifier_id == classifier_id)
        ).scalar_one_or_none()

    def get_classifiers_by_administrator(self, administrator_id: int) -> List[EducationClassifier]:
        return self.session.execute(
            select(EducationClassifier)
            .where(EducationClassifier.administrator_id == administrator_id)
        ).scalars().all()

    def get_classifiers_by_discipline(self, discipline_id: int) -> List[EducationClassifier]:
        return self.session.execute(
            select(EducationClassifier)
            .where(EducationClassifier.discipline_id == discipline_id)
        ).scalars().all()

    def create_classifier(
        self,
        name: str,
        administrator_id: int,
        discipline_id: int,
        created_at: Optional[datetime] = None
    ) -> EducationClassifier:
        try:
            classifier = EducationClassifier(
                name=name,
                created_at=created_at or datetime.utcnow(),
                administrator_id=administrator_id,
                discipline_id=discipline_id
            )
            self.session.add(classifier)
            self.session.commit()
            return classifier
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при создании классификатора: {str(e)}")

    def update_classifier(
        self,
        classifier_id: int,
        name: Optional[str] = None,
        administrator_id: Optional[int] = None,
        discipline_id: Optional[int] = None
    ) -> Optional[EducationClassifier]:
        classifier = self.get_classifier_by_id(classifier_id)
        if not classifier:
            return None

        try:
            if name is not None:
                classifier.name = name
            if administrator_id is not None:
                classifier.administrator_id = administrator_id
            if discipline_id is not None:
                classifier.discipline_id = discipline_id

            self.session.commit()
            return classifier
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Ошибка при обновлении классификатора: {str(e)}")

    def delete_classifier(self, classifier_id: int) -> bool:
        classifier = self.get_classifier_by_id(classifier_id)
        if classifier:
            self.session.delete(classifier)
            self.session.commit()
            return True
        return False