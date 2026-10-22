from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.state import State


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return self.db.query(Appointment).filter(Appointment.id_appointments == appointment_id).first()

    def list_all(self) -> list[Appointment]:
        return self.db.query(Appointment).order_by(Appointment.fecha_hora).all()

    def list_by_doctor_user(self, user_id: int) -> list[Appointment]:
        return (
            self.db.query(Appointment)
            .join(Doctor, Doctor.id_doctors == Appointment.id_doctors)
            .filter(Doctor.id_user == user_id)
            .order_by(Appointment.fecha_hora)
            .all()
        )

    def list_by_patient(self, patient_id: int) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.id_patients == patient_id).all()

    def list_by_doctor(self, doctor_id: int) -> list[Appointment]:
        return self.db.query(Appointment).filter(Appointment.id_doctors == doctor_id).all()

    def get_active_patient(self, patient_id: int) -> Patient | None:
        return self.db.scalar(
            select(Patient).where(Patient.id_patients == patient_id, Patient.activo.is_(True))
        )

    def get_active_doctor(self, doctor_id: int) -> Doctor | None:
        return self.db.scalar(
            select(Doctor).where(Doctor.id_doctors == doctor_id, Doctor.activo.is_(True))
        )

    def get_state_by_name(self, name: str) -> State | None:
        return self.db.scalar(select(State).where(State.nom_estado == name))

    def list_appointment_states(self, names: tuple[str, ...]) -> list[State]:
        return list(
            self.db.scalars(
                select(State).where(State.nom_estado.in_(names)).order_by(State.id_estado)
            )
        )

    def has_schedule_conflict(
        self,
        doctor_id: int,
        fecha_hora: datetime,
        exclude_appointment_id: int | None = None,
    ) -> bool:
        statement = select(Appointment.id_appointments).where(
            Appointment.id_doctors == doctor_id,
            Appointment.fecha_hora == fecha_hora,
            Appointment.state.has(State.nom_estado.notin_(("CANCELADA", "NO_ASISTIO"))),
        )
        if exclude_appointment_id is not None:
            statement = statement.where(Appointment.id_appointments != exclude_appointment_id)
        return self.db.scalar(statement.limit(1)) is not None

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
