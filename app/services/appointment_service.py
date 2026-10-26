from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentIngresoUpdate,
    AppointmentUpdate,
)


WAITING_ROOM_STATE = "EN SALA DE ESPERA"
APPOINTMENT_STATES = (
    "PROGRAMADA",
    "CONFIRMADA",
    WAITING_ROOM_STATE,
    "ATENDIDA",
    "CANCELADA",
    "NO_ASISTIO",
)
INACTIVE_STATES = {"CANCELADA", "NO_ASISTIO", "ATENDIDA"}


class AppointmentService:
    def __init__(self, db: Session):
        self.repo = AppointmentRepository(db)

    def list_states(self) -> list[str]:
        found = {state.nom_estado for state in self.repo.list_appointment_states(APPOINTMENT_STATES)}
        return [name for name in APPOINTMENT_STATES if name in found]

    def create_appointment(self, data: AppointmentCreate, user: User) -> Appointment:
        self._validate_schedule(data.id_patients, data.id_doctors, data.fecha_hora)
        state = self.repo.get_state_by_name(data.estado)
        if state is None:
            raise ValueError(f"El estado de cita '{data.estado}' no está configurado")
        appointment = Appointment(
            id_patients=data.id_patients,
            id_doctors=data.id_doctors,
            fecha_hora=data.fecha_hora,
            id_estado=state.id_estado,
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

    def list_appointments(self, user: User | None = None) -> list[Appointment]:
        permissions = set(user.role.permisos if user and user.role else [])
        if user is not None and "appointments.manage" not in permissions:
            return self.repo.list_by_doctor_user(user.id)
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
        if appointment.nom_estado in INACTIVE_STATES and (
            data.estado is None or data.estado == appointment.nom_estado
        ):
            raise ValueError("No se puede modificar una cita atendida, cancelada o que no asistió sin cambiar su estado")
        new_state_name = data.estado or appointment.nom_estado
        if new_state_name not in APPOINTMENT_STATES:
            raise ValueError(f"Estado de cita no permitido: '{new_state_name}'")
        state = self.repo.get_state_by_name(new_state_name)
        if state is None:
            raise ValueError(f"El estado de cita '{new_state_name}' no está configurado")
        if new_state_name not in INACTIVE_STATES:
            self._validate_schedule(
                appointment.id_patients,
                data.id_doctors,
                data.fecha_hora,
                exclude_appointment_id=appointment_id,
            )
        appointment.id_doctors = data.id_doctors
        appointment.fecha_hora = data.fecha_hora
        appointment.id_estado = state.id_estado
        appointment.state = state
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

    def register_ingreso(
        self,
        appointment_id: int,
        data: AppointmentIngresoUpdate,
        user: User,
    ) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
        if appointment.nom_estado not in {"PROGRAMADA", "CONFIRMADA", WAITING_ROOM_STATE}:
            raise ValueError("Solo se puede dar ingreso a citas programadas, confirmadas o en sala de espera")
        if data.fec_dilatacion is not None and data.fec_dilatacion < data.fec_ingreso:
            raise ValueError("La fecha de dilatación no puede ser anterior a la fecha de ingreso")
        state = self.repo.get_state_by_name(WAITING_ROOM_STATE)
        if state is None:
            raise ValueError(f"El estado de cita '{WAITING_ROOM_STATE}' no está configurado")
        appointment.id_estado = state.id_estado
        appointment.state = state
        appointment.fec_ingreso = data.fec_ingreso
        appointment.fec_dilatacion = data.fec_dilatacion
        appointment.prioridad = data.prioridad
        appointment.usu_actualizacion = user.id
        appointment.fec_actualizacion = datetime.now(timezone.utc)
        self.repo.db.add(
            AuditLog(
                user_id=user.id,
                accion="CHECKIN_APPOINTMENT",
                detalle={"id_appointments": appointment_id},
            )
        )
        return self._commit(appointment)

    def finalize_appointment(self, appointment_id: int, user: User) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
        permissions = set(user.role.permisos if user and user.role else [])
        if "appointments.manage" not in permissions:
            own_ids = {item.id_appointments for item in self.repo.list_by_doctor_user(user.id)}
            if appointment_id not in own_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La cita no pertenece al médico autenticado")
        if appointment.nom_estado not in {"PROGRAMADA", "CONFIRMADA", WAITING_ROOM_STATE}:
            raise ValueError("Solo se pueden finalizar citas programadas, confirmadas o en sala de espera")
        state = self.repo.get_state_by_name("ATENDIDA")
        if state is None:
            raise ValueError("El estado de cita 'ATENDIDA' no está configurado")
        finished_at = datetime.now(timezone.utc)
        appointment.id_estado = state.id_estado
        appointment.state = state
        try:
            self.repo.db.flush()
            self.repo.finalize(appointment_id, finished_at, user.id)
        except DBAPIError as exc:
            self.repo.db.rollback()
            raise ValueError(str(getattr(exc.orig, "args", [exc])[0]).splitlines()[0]) from exc
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
