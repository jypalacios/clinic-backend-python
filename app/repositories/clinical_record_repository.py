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

    @staticmethod
    def _like(term: str | None) -> str | None:
        if not term or not term.strip():
            return None
        escaped = term.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"

    def list_enabled_cups(self, term: str | None = None, limit: int | None = None) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT id_cup, codigo, nombre FROM v_cups WHERE habilitado "
                    "AND (CAST(:q AS text) IS NULL OR codigo ILIKE :q OR nombre ILIKE :q) "
                    "ORDER BY codigo LIMIT :lim"
                ),
                {"q": self._like(term), "lim": limit},
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

    def list_enabled_diagnoses(self, term: str | None = None, limit: int | None = None) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT id_diag, codigo, titulo FROM cli_diagnoses WHERE activo "
                    "AND (CAST(:q AS text) IS NULL OR codigo ILIKE :q OR titulo ILIKE :q) "
                    "ORDER BY codigo LIMIT :lim"
                ),
                {"q": self._like(term), "lim": limit},
            ).mappings()
        ]

    def assign_diagnoses(self, entry_id: int, diag_ids: list[int], user_id: int) -> None:
        for diag_id in diag_ids:
            self.db.execute(
                text("CALL sp_crear_cli_diag_hc(:diag, :entry, :user)"),
                {"diag": diag_id, "entry": entry_id, "user": user_id},
            )

    def diagnoses_by_entry(self, entry_ids: list[int]) -> dict[int, list[dict]]:
        if not entry_ids:
            return {}
        rows = self.db.execute(
            text(
                "SELECT dh.id_entries, d.id_diag, d.codigo, d.titulo AS diagnostico "
                "FROM cli_diag_hc dh JOIN cli_diagnoses d ON d.id_diag = dh.id_diag "
                "WHERE dh.id_entries = ANY(:ids) ORDER BY dh.id_diag_hc"
            ),
            {"ids": entry_ids},
        ).mappings()
        result: dict[int, list[dict]] = {}
        for row in rows:
            result.setdefault(row["id_entries"], []).append(
                {"id_diag": row["id_diag"], "codigo": row["codigo"], "diagnostico": row["diagnostico"]}
            )
        return result

    def entries_by_id(self, entry_ids: list[int]) -> dict[int, dict]:
        if not entry_ids:
            return {}
        rows = self.db.execute(
            text(
                "SELECT DISTINCT id_entries, id_clinics, id_doctors, id_entries_rectifica, "
                "fec_entrada, motivo_consulta, examen_fisico, diagnostico_texto AS diagnostico, "
                "plan, formulacion, notas, peso, talle, medico, trim(nom_espect) AS nom_espect "
                "FROM v_clinical_entries WHERE id_entries = ANY(:ids)"
            ),
            {"ids": entry_ids},
        ).mappings()
        return {row["id_entries"]: dict(row) for row in rows}

    def get_entry(self, entry_id: int) -> ClinicalEntry | None:
        return self.db.get(ClinicalEntry, entry_id)

    def insert_entry(self, record_id: int, doctor_id: int, rectifies: int | None, data: dict, user_id: int) -> int:
        measures = [
            m for m in data.get("medidas") or []
            if m.get("derecho") or m.get("izquierdo") or m.get("detalle")
        ]
        first = measures[0] if measures else None
        entry_id = self.db.execute(
            text(
                "CALL sp_insertar_clinical_entry(NULL::bigint, :record, :doctor, :motivo, :examen, "
                ":diag, :plan, :formulacion, :notas, :usuario, NULL::inet, :peso, :talle, "
                ":detalle_id, :derecho, :izquierdo, :rectifica, NULL::text, NULL::text, :detalle)"
            ),
            {
                "record": record_id,
                "doctor": doctor_id,
                "motivo": data["motivo_consulta"],
                "examen": data.get("examen_fisico"),
                "diag": data.get("diagnostico"),
                "plan": data.get("plan"),
                "formulacion": data.get("formulacion"),
                "notas": data.get("notas"),
                "usuario": user_id,
                "peso": data.get("peso"),
                "talle": data.get("talle"),
                "detalle_id": first["id_hc_detalle"] if first else None,
                "derecho": first.get("derecho") if first else None,
                "izquierdo": first.get("izquierdo") if first else None,
                "detalle": first.get("detalle") if first else None,
                "rectifica": rectifies,
            },
        ).scalar_one()
        for extra in measures[1:]:
            self.db.execute(
                text(
                    "INSERT INTO cli_hc_medida (id_hc_detalle, derecho, izquierdo, id_entries, detalle) "
                    "VALUES (:detalle_id, :derecho, :izquierdo, :entry, :detalle)"
                ),
                {
                    "detalle_id": extra["id_hc_detalle"],
                    "derecho": extra.get("derecho"),
                    "izquierdo": extra.get("izquierdo"),
                    "detalle": extra.get("detalle"),
                    "entry": entry_id,
                },
            )
        return entry_id

    def list_measure_types(self, specialty_id: int | None = None) -> list[dict]:
        specialty_filter = "WHERE g.id_espect = :specialty_id " if specialty_id is not None else ""
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT d.id_hc_detalle, d.id_hc_general, trim(d.det_hc_general) AS detalle, "
                    "trim(g.det_hcgeneral) AS general FROM cli_hc_detalle d "
                    "JOIN cli_hc_general g ON g.id_hcgeneral = d.id_hc_general "
                    f"{specialty_filter}"
                    "ORDER BY g.det_hcgeneral, d.det_hc_general"
                ),
                {"specialty_id": specialty_id},
            ).mappings()
        ]

    def measures_by_entry(self, entry_ids: list[int]) -> dict[int, list[dict]]:
        if not entry_ids:
            return {}
        rows = self.db.execute(
            text(
                "SELECT DISTINCT id_entries, id_hc_medida, id_hc_detalle, "
                "trim(detalle_medida) AS detalle_medida, trim(det_hcgeneral) AS general, "
                "trim(derecho) AS derecho, trim(izquierdo) AS izquierdo, "
                "trim(det_derecho) AS det_derecho, trim(det_izquierdo) AS det_izquierdo, "
                "trim(detalle) AS detalle "
                "FROM v_clinical_entries_espect "
                "WHERE id_entries = ANY(:ids) ORDER BY id_hc_medida"
            ),
            {"ids": entry_ids},
        ).mappings()
        result: dict[int, list[dict]] = {}
        for row in rows:
            result.setdefault(row["id_entries"], []).append(
                {k: v for k, v in row.items() if k != "id_entries"}
            )
        return result

    def add(self, item: ClinicalRecord | ClinicalEntry) -> None:
        self.db.add(item)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
