from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientCreate


class PatientService:
    def __init__(self, db: Session):
        self.repo = PatientRepository(db)

    def create_patient(self, data: PatientCreate) -> Patient:
        if not self.repo.get_document(data.id_documents):
            raise ValueError("El tipo de documento seleccionado no existe")
        if self.repo.get_by_identification(data.id_documents, data.ced_patients):
            raise ValueError("El número de identificación ya existe para este tipo de documento")

        patient = Patient(
            ced_patients=data.ced_patients,
            id_documents=data.id_documents,
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

    def list_patients(self, user: User) -> list[Patient]:
        permissions = set(user.role.permisos if user.role else [])
        if "patients.view" in permissions:
            return self.repo.list_all()
        return self.repo.list_for_doctor(user.id)

    def get_patient(self, patient_id: int, user: User) -> Patient | None:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            return None
        permissions = set(user.role.permisos if user.role else [])
        if "patients.view" not in permissions and not self.repo.is_assigned_to_doctor(patient_id, user.id):
            return None
        return patient
