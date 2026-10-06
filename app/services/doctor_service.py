from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.role import Role
from app.models.user import User
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor_schema import DoctorCreate


class DoctorService:
    def __init__(self, db: Session):
        self.repo = DoctorRepository(db)

    def create_doctor(self, data: DoctorCreate, created_by: int | None = None) -> Doctor:
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
            usu_creacion=created_by,
        )

        return self.repo.create(doctor)

    def list_doctors(self) -> list[Doctor]:
        return self.repo.list_all()

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        return self.repo.get_by_id(doctor_id)

    def link_user(self, doctor_id: int, user_id: int | None, updated_by: int) -> Doctor:
        doctor = self.repo.get_by_id(doctor_id)
        if not doctor:
            raise ValueError("Médico no encontrado")
        if not doctor.activo:
            raise ValueError("No se puede vincular una cuenta a un médico inactivo")
        if user_id is not None:
            user = self.repo.db.get(User, user_id)
            if not user or user.id_estado != 1:
                raise ValueError("La cuenta seleccionada no existe o está inactiva")
            role = self.repo.db.get(Role, user.id_role)
            role_name = role.nom_role.strip().casefold() if role else ""
            if role_name not in {"medico", "médico", "doctor"}:
                raise ValueError("Solo se pueden vincular cuentas con rol médico")
            linked_doctor = (
                self.repo.db.query(Doctor)
                .filter(Doctor.id_user == user_id, Doctor.id_doctors != doctor_id)
                .first()
            )
            if linked_doctor:
                raise ValueError("La cuenta ya está vinculada a otro médico")
        doctor.id_user = user_id
        doctor.usu_actualizacion = updated_by
        doctor.fec_actualizacion = datetime.now(timezone.utc)
        self.repo.db.add(
            AuditLog(
                user_id=updated_by,
                accion="LINK_DOCTOR_USER",
                detalle={"id_doctors": doctor_id, "id_user": user_id} if user_id is not None else {"id_doctors": doctor_id},
            )
        )
        return self.repo.update(doctor)
