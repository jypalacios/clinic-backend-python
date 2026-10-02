from datetime import datetime

from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return self.db.query(Appointment).filter(Appointment.id_appointments == appointment_id).first()

    def list_all(self) -> list[Appointment]:
        return self.db.query(Appointment).all()

    def list_by_patient(self, patient_id: int) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.id_patients == patient_id).all()

    def list_by_doctor(self, doctor_id: int) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.id_doctors == doctor_id).all()

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def update(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def delete(self, appointment: Appointment) -> None:
        self.db.delete(appointment)
        self.db.commit()
