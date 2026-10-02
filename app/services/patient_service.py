from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientCreate


class PatientService:
    def __init__(self, db: Session):
        self.repo = PatientRepository(db)

    def create_patient(self, data: PatientCreate) -> Patient:
        if self.repo.get_by_cedula(data.ced_patients):
            raise ValueError("La cédula del paciente ya existe")

        patient = Patient(
            ced_patients=data.ced_patients,
            nom_patients=data.nom_patients,
            ape_patients=data.ape_patients,
            fec_nacimiento=data.fec_nacimiento,
            id_sexo=data.id_sexo,
            telefono=data.telefono,
            email=data.email,
            direccion=data.direccion,
            eps=data.eps,
            contacto_emergencia=data.contacto_emergencia,
        )

        return self.repo.create(patient)

    def list_patients(self) -> list[Patient]:
        return self.repo.list_all()

    def get_patient(self, patient_id: int) -> Patient | None:
        return self.repo.get_by_id(patient_id)
