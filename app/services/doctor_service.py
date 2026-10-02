from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor_schema import DoctorCreate


class DoctorService:
    def __init__(self, db: Session):
        self.repo = DoctorRepository(db)

    def create_doctor(self, data: DoctorCreate) -> Doctor:
        if self.repo.get_by_email(str(data.email)) if data.email else False:
            raise ValueError("El email del médico ya existe")

        doctor = Doctor(
            ape_doctors=data.ape_doctors,
            nom_doctors=data.nom_doctors,
            id_espect=data.id_espect,
            id_sexo=data.id_sexo,
            telefono=data.telefono,
            email=data.email,
            direccion=data.direccion,
        )

        return self.repo.create(doctor)

    def list_doctors(self) -> list[Doctor]:
        return self.repo.list_all()

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        return self.repo.get_by_id(doctor_id)
