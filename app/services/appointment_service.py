from datetime import datetime

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment_schema import AppointmentCreate


class AppointmentService:
    def __init__(self, db: Session):
        self.repo = AppointmentRepository(db)

    def create_appointment(self, data: AppointmentCreate) -> Appointment:
        appointment = Appointment(
            id_patients=data.id_patients,
            id_doctors=data.id_doctors,
            fecha_hora=data.fecha_hora,
            estado=data.estado,
        )

        return self.repo.create(appointment)

    def list_appointments(self) -> list[Appointment]:
        return self.repo.list_all()

    def get_appointment(self, appointment_id: int) -> Appointment | None:
        return self.repo.get_by_id(appointment_id)
