from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.appointment import Appointment
from app.models.state import State
from app.models.clinical_record import ClinicalEntry, ClinicalRecord
from app.models.doctor import Doctor
from app.models.patient import Patient


class ClinicalRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, doctor_id: int | None, include_archived: bool) -> list[ClinicalRecord]:
        statement = (
            select(ClinicalRecord)
            .options(
                joinedload(ClinicalRecord.patient).joinedload(Patient.sexo),
                joinedload(ClinicalRecord.doctor),
                selectinload(ClinicalRecord.entries).joinedload(ClinicalEntry.doctor),
            )
            .order_by(ClinicalRecord.fec_creacion.desc(), ClinicalRecord.id_clinic.desc())
        )
        if not include_archived:
            statement = statement.where(ClinicalRecord.activo.is_(True))
        if doctor_id is not None:
            statement = statement.where(ClinicalRecord.id_doctors == doctor_id)
        return list(self.db.scalars(statement).unique().all())

    def get_record(self, record_id: int) -> ClinicalRecord | None:
        statement = (
            select(ClinicalRecord)
            .options(
                joinedload(ClinicalRecord.patient).joinedload(Patient.sexo),
                joinedload(ClinicalRecord.doctor),
                selectinload(ClinicalRecord.entries).joinedload(ClinicalEntry.doctor),
            )
            .where(ClinicalRecord.id_clinic == record_id)
        )
        return self.db.scalars(statement).unique().one_or_none()

    def get_patient(self, patient_id: int) -> Patient | None:
        return self.db.get(Patient, patient_id)

    def get_doctor_for_user(self, user_id: int) -> Doctor | None:
        statement = select(Doctor).where(Doctor.id_user == user_id, Doctor.activo.is_(True))
        return self.db.scalars(statement).one_or_none()

    def doctor_has_patient_appointment(self, doctor_id: int, patient_id: int) -> bool:
        statement = (
            select(Appointment.id_appointments)
            .where(
                Appointment.id_doctors == doctor_id,
                Appointment.id_patients == patient_id,
                Appointment.state.has(State.nom_estado.notin_(("CANCELADA", "NO_ASISTIO"))),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def list_enabled_cups(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text("SELECT id_cup, codigo, nombre FROM v_cups WHERE habilitado ORDER BY codigo")
            ).mappings()
        ]

    def list_patient_cups(self, patient_id: int) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT v.id_cup_patient, v.id_cup, c.codigo, c.nombre, "
                    "v.activo, v.fec_creacion FROM v_cli_cups_patients v "
                    "JOIN cli_cups c ON c.id_cup = v.id_cup "
                    "WHERE v.id_patients = :patient AND COALESCE(v.activo, true) "
                    "ORDER BY v.fec_creacion DESC, v.id_cup_patient DESC"
                ),
                {"patient": patient_id},
            ).mappings()
        ]

    def assign_cups(self, patient_id: int, cup_ids: list[int], user_id: int) -> None:
        for cup_id in cup_ids:
            self.db.execute(
                text("CALL sp_insertar_cli_cups_patients(NULL::integer, :cup, :patient, true, :user)"),
                {"cup": cup_id, "patient": patient_id, "user": user_id},
            )

    def get_entry(self, entry_id: int) -> ClinicalEntry | None:
        return self.db.get(ClinicalEntry, entry_id)

    def add(self, item: ClinicalRecord | ClinicalEntry) -> None:
        self.db.add(item)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
