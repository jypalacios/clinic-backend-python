from typing import Any
from unicodedata import combining, normalize

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

        self._validate_measures(data, doctor)
        record = ClinicalRecord(id_patients=data.id_patients, id_doctors=doctor.id_doctors)
        try:
            self.repo.add(record)
            self.repo.flush()
            entry_id_new = self.repo.insert_entry(
                record.id_clinic,
                doctor.id_doctors,
                None,
                data.model_dump(exclude={"id_patients", "id_cups", "id_diags"}),
                user.id,
            )
            self._assign_diagnoses(data.id_diags, entry_id_new, user.id)
            self._assign_cups(data.id_cups, data.id_patients, user.id)
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

        self._validate_measures(data, doctor)
        try:
            new_entry_id = self.repo.insert_entry(
                record_id,
                doctor.id_doctors,
                entry_id,
                data.model_dump(exclude={"id_cups", "id_diags"}),
                user.id,
            )
            self._assign_diagnoses(data.id_diags, new_entry_id, user.id)
            self._assign_cups(data.id_cups, record.id_patients, user.id)
            self._audit(
                user.id,
                "CORRECT_CLINICAL_ENTRY" if entry_id is not None else "ADD_CLINICAL_ENTRY",
                {"id_clinic": record_id, "id_entries": new_entry_id, **(
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

    def list_cups(self, term: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return self.repo.list_enabled_cups(term, limit)

    def list_patient_cups(self, patient_id: int, user: User) -> list[dict[str, Any]]:
        role_name = user.role.nom_role.strip().casefold() if user.role else ""
        if role_name in {"medico", "médico", "doctor"}:
            doctor = self._current_doctor(user)
            record = self.db.scalars(
                select(ClinicalRecord).where(
                    ClinicalRecord.id_patients == patient_id,
                    ClinicalRecord.id_doctors == doctor.id_doctors,
                )
            ).first()
            if not record and not self.repo.doctor_has_patient_appointment(doctor.id_doctors, patient_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puede consultar CUPS de pacientes con cita o historia asignada",
                )
        return self.repo.list_patient_cups(patient_id)

    def list_diagnoses(self, term: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return self.repo.list_enabled_diagnoses(term, limit)

    def list_measure_types(self, user: User) -> list[dict[str, Any]]:
        return self.repo.list_measure_types(self._current_doctor(user).id_espect)

    @staticmethod
    def _measure_mode(specialty_name: str) -> str:
        name = "".join(char for char in normalize("NFD", specialty_name.strip().casefold()) if not combining(char))
        return "detalle" if name in {"neurologia", "neurologo", "neurologa"} else "ojos"

    def measure_config(self, user: User) -> dict[str, Any]:
        doctor = self._current_doctor(user)
        return {
            "mode": self._measure_mode(doctor.specialty.nom_espect),
            "types": self.repo.list_measure_types(doctor.id_espect),
        }

    def _validate_measures(self, data: ClinicalEntryCreate, doctor: Doctor) -> None:
        if not data.medidas:
            return
        valid = {item["id_hc_detalle"] for item in self.repo.list_measure_types(doctor.id_espect)}
        if any(measure.id_hc_detalle not in valid for measure in data.medidas):
            raise ValueError("Una o más medidas no corresponden a la especialidad del médico")
        if self._measure_mode(doctor.specialty.nom_espect) == "detalle" and any(
            measure.derecho or measure.izquierdo for measure in data.medidas
        ):
            raise ValueError("Las medidas de neurología deben registrarse en el campo detalle, no en los campos de ojos")

    def _assign_diagnoses(self, diag_ids: list[int], entry_id: int, user_id: int) -> None:
        unique_ids = list(dict.fromkeys(diag_ids))
        if not unique_ids:
            return
        valid = {diag["id_diag"] for diag in self.repo.list_enabled_diagnoses()}
        if any(diag_id not in valid for diag_id in unique_ids):
            raise ValueError("Uno o más diagnósticos seleccionados no existen o están inactivos")
        self.repo.assign_diagnoses(entry_id, unique_ids, user_id)

    def _assign_cups(self, cup_ids: list[int], patient_id: int, user_id: int) -> None:
        unique_ids = list(dict.fromkeys(cup_ids))
        if not unique_ids:
            return
        valid = {cup["id_cup"] for cup in self.repo.list_enabled_cups()}
        if any(cup_id not in valid for cup_id in unique_ids):
            raise ValueError("Uno o más CUPS seleccionados no existen o están inactivos")
        self.repo.assign_cups(patient_id, unique_ids, user_id)

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

    def _serialize_record(self, record: ClinicalRecord, include_entries: bool) -> dict[str, Any]:
        entries = []
        if include_entries:
            entry_ids = [entry.id_entries for entry in record.entries]
            entry_data = self.repo.entries_by_id(entry_ids)
            diagnoses = self.repo.diagnoses_by_entry(entry_ids)
            measures = self.repo.measures_by_entry(entry_ids)
            for entry in record.entries:
                if entry.id_entries not in entry_data:
                    raise RuntimeError(f"La nota clínica {entry.id_entries} no se encuentra en v_clinical_entries")
                entries.append({
                    **entry_data[entry.id_entries],
                    "measure_mode": self._measure_mode(entry_data[entry.id_entries]["nom_espect"]),
                    "medidas": measures.get(entry.id_entries, []),
                    "diagnosticos": diagnoses.get(entry.id_entries, []),
                })
        return {
            "id_clinic": record.id_clinic,
            "id_patients": record.id_patients,
            "patient": {
                "id_patients": record.patient.id_patients,
                "ced_patients": record.patient.ced_patients,
                "nom_patients": record.patient.nom_patients,
                "ape_patients": record.patient.ape_patients,
                "edad": record.patient.edad,
                "nom_sexo": record.patient.sexo.nom_sexo,
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
