from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.specialty import Specialty
from app.repositories.specialty_repository import SpecialtyRepository
from app.schemas.specialty_schema import SpecialtyCreate


class SpecialtyService:
    def __init__(self, db: Session):
        self.repo = SpecialtyRepository(db)
        self.db = db

    def list_specialties(self) -> list[Specialty]:
        return self.repo.list_all()

    def create_specialty(self, data: SpecialtyCreate) -> Specialty:
        name = data.nom_espect.strip()
        if len(name) < 2:
            raise ValueError("El nombre de la especialidad debe tener al menos 2 caracteres")
        if self.repo.get_by_name(name):
            raise ValueError("La especialidad ya existe")

        specialty = Specialty(nom_espect=name)
        try:
            return self.repo.create(specialty)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("La especialidad ya existe") from exc
