from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.clinical_record import ClinicalEntry, ClinicalRecord
from app.models.doctor import Doctor
from app.models.user import User
from app.repositories.clinical_record_repository import ClinicalRecordRepository
from app.schemas.clinical_record_schema import ClinicalEntryCreate, ClinicalRecordCreate


class ClinicalRecordService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ClinicalRecordRepository(db)

    def list_records(self, user: User) -> list[dict[str, Any]]:
        role_name = user.role.nom_role.strip().casefold() if user.role else ""
        is_doctor = role_name in {"medico", "médico", "doctor"}
        doctor_id = None
        if is_doctor:
            doctor = self._current_doctor(user)
            doctor_id = doctor.id_doctors

        records = self.repo.list_all(
            doctor_id=doctor_id,
            include_archived=not is_doctor and "medical_history.delete" in (user.role.permisos if user.role else []),
        )
        return [self._serialize_record(record, include_entries=is_doctor) for record in records]

    def create_record(self, data: ClinicalRecordCreate, user: User) -> dict[str, Any]:
        doctor = self._current_doctor(user)
        patient = self.repo.get_patient(data.id_patients)
        if not patient or not patient.activo:
            raise ValueError("El paciente no existe o está inactivo")
        if not self.repo.doctor_has_patient_appointment(doctor.id_doctors, data.id_patients):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede abrir historias clínicas para pacientes con una cita asignada",
            )

        existing = self.db.scalars(
            select(ClinicalRecord).where(ClinicalRecord.id_patients == data.id_patients)
        ).one_or_none()
        if existing:
            if existing.activo:
                raise ValueError("El paciente ya tiene una historia clínica")
            raise ValueError("La historia está archivada; solicite al administrador que la restaure")

        record = ClinicalRecord(id_patients=data.id_patients, id_doctors=doctor.id_doctors)
        try:
            self.repo.add(record)
            self.repo.flush()
            entry = ClinicalEntry(
                id_clinics=record.id_clinic,
                id_doctors=doctor.id_doctors,
                **data.model_dump(exclude={"id_patients"}),
            )
            self.repo.add(entry)
            self._audit(user.id, "CREATE_CLINICAL_RECORD", {"id_clinic": record.id_clinic})
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

        saved = self.repo.get_record(record.id_clinic)
        if saved is None:
            raise RuntimeError("La historia clínica creada no pudo recuperarse")
        return self._serialize_record(saved, include_entries=True)

    def append_entry(
        self,
        record_id: int,
        data: ClinicalEntryCreate,
        entry_id: int | None,
        user: User,
    ) -> dict[str, Any]:
        doctor = self._current_doctor(user)
        record = self.repo.get_record(record_id)
        self._ensure_owned_active_record(record, doctor)
        if entry_id is not None:
            original = self.repo.get_entry(entry_id)
            if not original or original.id_clinics != record_id:
                raise ValueError("La nota que intenta rectificar no pertenece a esta historia")

        entry = ClinicalEntry(
            id_clinics=record_id,
            id_doctors=doctor.id_doctors,
            id_entries_rectifica=entry_id,
            **data.model_dump(),
        )
        try:
            self.repo.add(entry)
            self.repo.flush()
            self._audit(
                user.id,
                "CORRECT_CLINICAL_ENTRY" if entry_id is not None else "ADD_CLINICAL_ENTRY",
                {"id_clinic": record_id, "id_entries": entry.id_entries, **(
                    {"id_entries_rectifica": entry_id} if entry_id is not None else {}
                )},
            )
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

        saved = self.repo.get_record(record_id)
        if saved is None:
            raise RuntimeError("La historia clínica actualizada no pudo recuperarse")
        return self._serialize_record(saved, include_entries=True)

    def archive_record(self, record_id: int, user: User) -> None:
        record = self.repo.get_record(record_id)
        if not record:
            raise ValueError("Historia clínica no encontrada")
        if not record.activo:
            return
        record.activo = False
        try:
            self._audit(user.id, "ARCHIVE_CLINICAL_RECORD", {"id_clinic": record_id})
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

    def restore_record(self, record_id: int, user: User) -> None:
        record = self.repo.get_record(record_id)
        if not record:
            raise ValueError("Historia clínica no encontrada")
        if record.activo:
            return
        record.activo = True
        try:
            self._audit(user.id, "RESTORE_CLINICAL_RECORD", {"id_clinic": record_id})
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

    def _current_doctor(self, user: User) -> Doctor:
        doctor = self.repo.get_doctor_for_user(user.id)
        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Su cuenta aún no está vinculada a un perfil médico activo",
            )
        return doctor

    @staticmethod
    def _ensure_owned_active_record(record: ClinicalRecord | None, doctor: Doctor) -> None:
        if record is None:
            raise ValueError("Historia clínica no encontrada")
        if not record.activo:
            raise ValueError("La historia clínica está archivada")
        if record.id_doctors != doctor.id_doctors:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el médico tratante puede agregar o rectificar notas de esta historia",
            )

    def _audit(self, user_id: int, action: str, details: dict[str, int]) -> None:
        self.repo.add(AuditLog(user_id=user_id, accion=action, detalle=details))

    @staticmethod
    def _serialize_record(record: ClinicalRecord, include_entries: bool) -> dict[str, Any]:
        entries = []
        if include_entries:
            for entry in record.entries:
                entries.append({
                    "id_entries": entry.id_entries,
                    "id_clinics": entry.id_clinics,
                    "id_doctors": entry.id_doctors,
                    "id_entries_rectifica": entry.id_entries_rectifica,
                    "fec_entrada": entry.fec_entrada,
                    "motivo_consulta": entry.motivo_consulta,
                    "examen_fisico": entry.examen_fisico,
                    "diagnostico": entry.diagnostico,
                    "plan": entry.plan,
                    "formulacion": entry.formulacion,
                    "notas": entry.notas,
                    "medico": f"{entry.doctor.nom_doctors} {entry.doctor.ape_doctors}".strip(),
                })
        return {
            "id_clinic": record.id_clinic,
            "id_patients": record.id_patients,
            "patient": {
                "id_patients": record.patient.id_patients,
                "ced_patients": record.patient.ced_patients,
                "nom_patients": record.patient.nom_patients,
                "ape_patients": record.patient.ape_patients,
            },
            "id_doctors": record.id_doctors,
            "doctor": {
                "id_doctors": record.doctor.id_doctors,
                "nom_doctors": record.doctor.nom_doctors,
                "ape_doctors": record.doctor.ape_doctors,
            },
            "fec_creacion": record.fec_creacion,
            "activo": record.activo,
            "total_entradas": len(record.entries),
            "entries": entries,
        }
