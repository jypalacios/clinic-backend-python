from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment_schema import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    def __init__(self, db: Session):
        self.repo = AppointmentRepository(db)

    def create_appointment(self, data: AppointmentCreate, user: User) -> Appointment:
        self._validate_schedule(data.id_patients, data.id_doctors, data.fecha_hora)
        appointment = Appointment(
            id_patients=data.id_patients,
            id_doctors=data.id_doctors,
            fecha_hora=data.fecha_hora,
            estado=data.estado,
            usu_creacion=user.id,
        )
        self.repo.db.add(appointment)
        self.repo.db.flush()
        self.repo.db.add(
            AuditLog(
                user_id=user.id,
                accion="CREATE_APPOINTMENT",
                detalle={"id_appointments": appointment.id_appointments},
            )
        )
        return self._commit(appointment)

    def list_appointments(self) -> list[Appointment]:
        return self.repo.list_all()

    def get_appointment(self, appointment_id: int) -> Appointment | None:
        return self.repo.get_by_id(appointment_id)

    def update_appointment(
        self,
        appointment_id: int,
        data: AppointmentUpdate,
        user: User,
    ) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
        if appointment.estado not in {"PROGRAMADA", "CONFIRMADA"}:
            raise ValueError("Solo se pueden reprogramar citas programadas o confirmadas")
        self._validate_schedule(
            appointment.id_patients,
            data.id_doctors,
            data.fecha_hora,
            exclude_appointment_id=appointment_id,
        )
        appointment.id_doctors = data.id_doctors
        appointment.fecha_hora = data.fecha_hora
        appointment.usu_actualizacion = user.id
        appointment.fec_actualizacion = datetime.now(timezone.utc)
        self.repo.db.add(
            AuditLog(
                user_id=user.id,
                accion="RESCHEDULE_APPOINTMENT",
                detalle={"id_appointments": appointment_id},
            )
        )
        return self._commit(appointment)

    def _validate_schedule(
        self,
        patient_id: int,
        doctor_id: int,
        fecha_hora: datetime,
        exclude_appointment_id: int | None = None,
    ) -> None:
        if not self.repo.get_active_patient(patient_id):
            raise ValueError("El paciente no existe o está inactivo")
        if not self.repo.get_active_doctor(doctor_id):
            raise ValueError("El médico no existe o está inactivo")
        if fecha_hora <= datetime.now(timezone.utc):
            raise ValueError("La fecha y hora de la cita deben ser futuras")
        if self.repo.has_schedule_conflict(doctor_id, fecha_hora, exclude_appointment_id):
            raise ValueError("El médico ya tiene una cita activa en esa fecha y hora")

    def _commit(self, appointment: Appointment) -> Appointment:
        try:
            self.repo.db.commit()
            self.repo.db.refresh(appointment)
        except IntegrityError as exc:
            self.repo.db.rollback()
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if constraint == "ux_appointments_doctor_hora":
                raise ValueError("El médico ya tiene una cita activa en esa fecha y hora") from exc
            raise
        return appointment
