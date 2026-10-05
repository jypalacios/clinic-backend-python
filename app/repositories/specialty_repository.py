from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.specialty import Specialty


class SpecialtyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Specialty]:
        return self.db.query(Specialty).order_by(Specialty.nom_espect).all()

    def get_by_name(self, name: str) -> Specialty | None:
        return self.db.query(Specialty).filter(func.lower(Specialty.nom_espect) == name.lower()).first()

    def create(self, specialty: Specialty) -> Specialty:
        self.db.add(specialty)
        self.db.commit()
        self.db.refresh(specialty)
        return specialty
