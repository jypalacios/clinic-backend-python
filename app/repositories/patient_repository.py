from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
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

    def list_for_doctor(self, user_id: int) -> list[Patient]:
        statement = (
            select(Patient)
            .join(Appointment, Appointment.id_patients == Patient.id_patients)
            .join(Doctor, Doctor.id_doctors == Appointment.id_doctors)
            .where(
                Doctor.id_user == user_id,
                Doctor.activo.is_(True),
                Patient.activo.is_(True),
                Appointment.estado.notin_(("CANCELADA", "NO_ASISTIO")),
            )
            .distinct()
            .order_by(Patient.ape_patients, Patient.nom_patients)
        )
        return list(self.db.scalars(statement).all())

    def is_assigned_to_doctor(self, patient_id: int, user_id: int) -> bool:
        statement = (
            select(Appointment.id_appointments)
            .join(Doctor, Doctor.id_doctors == Appointment.id_doctors)
            .where(
                Appointment.id_patients == patient_id,
                Doctor.id_user == user_id,
                Doctor.activo.is_(True),
                Patient.activo.is_(True),
                Appointment.estado.notin_(("CANCELADA", "NO_ASISTIO")),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

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
