from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: int) -> Patient | None:
        return self.db.query(Patient).filter(Patient.id_patients == patient_id).first()

    def get_by_cedula(self, cedula: str) -> Patient | None:
        return self.db.query(Patient).filter(Patient.ced_patients == cedula).first()

    def list_all(self) -> list[Patient]:
        return self.db.query(Patient).all()

    def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def update(self, patient: Patient) -> Patient:
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def delete(self, patient: Patient) -> None:
        self.db.delete(patient)
        self.db.commit()
