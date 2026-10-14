from sqlalchemy import Integer, String, column, select, table, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.document import DocumentCatalog
from app.models.patient import Patient
from app.models.sexo import Sexo


sexo_view = table(
    "v_sexo",
    column("id_sexo", Integer),
    column("nom_sexo", String),
)


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: int) -> Patient | None:
        result = (
            self.db.query(Patient, sexo_view.c.nom_sexo)
            .options(joinedload(Patient.document))
            .join(sexo_view, sexo_view.c.id_sexo == Patient.id_sexo)
            .filter(Patient.id_patients == patient_id)
            .first()
        )
        if result is None:
            return None
        patient, nom_sexo = result
        setattr(patient, "nom_sexo", nom_sexo)
        return patient

    def get_by_identification(self, document_id: int, identification: str) -> Patient | None:
        return (
            self.db.query(Patient)
            .filter(
                Patient.id_documents == document_id,
                Patient.ced_patients == identification,
            )
            .first()
        )

    def list_all(self) -> list[Patient]:
        results = (
            self.db.query(Patient, sexo_view.c.nom_sexo)
            .options(joinedload(Patient.document))
            .join(sexo_view, sexo_view.c.id_sexo == Patient.id_sexo)
            .order_by(Patient.ape_patients, Patient.nom_patients, Patient.id_patients)
            .all()
        )
        return self._attach_sexo_names(results)

    def list_sexos(self) -> list[Sexo]:
        return list(self.db.scalars(select(Sexo)).all())

    def list_documents(self) -> list[DocumentCatalog]:
        statement = select(DocumentCatalog).order_by(DocumentCatalog.id_documents)
        return list(self.db.scalars(statement).all())

    def get_document(self, document_id: int) -> DocumentCatalog | None:
        statement = select(DocumentCatalog).where(DocumentCatalog.id_documents == document_id)
        return self.db.scalar(statement)

    def existing_identifications(
        self,
        identifications: set[tuple[int, str]],
    ) -> set[tuple[int, str]]:
        if not identifications:
            return set()
        statement = select(Patient.id_documents, Patient.ced_patients).where(
            tuple_(Patient.id_documents, Patient.ced_patients).in_(identifications)
        )
        return set(self.db.execute(statement).tuples().all())

    def import_many(self, patients: list[Patient], user_id: int) -> int:
        try:
            self.db.add_all(patients)
            self.db.flush()
            self.db.add(
                AuditLog(
                    user_id=user_id,
                    accion="IMPORT_PATIENTS_CSV",
                    detalle={"imported_rows": len(patients), "source": "CSV"},
                )
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            diagnostic = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "patients_document_identification" in diagnostic:
                raise ValueError(
                    "Una o más identificaciones ya fueron registradas. No se importó ningún paciente; "
                    "vuelva a validar el archivo."
                ) from exc
            raise
        except Exception:
            self.db.rollback()
            raise
        return len(patients)

    def list_for_doctor(self, user_id: int) -> list[Patient]:
        statement = (
            select(Patient, sexo_view.c.nom_sexo).options(joinedload(Patient.document))
            .join(Appointment, Appointment.id_patients == Patient.id_patients)
            .join(Doctor, Doctor.id_doctors == Appointment.id_doctors)
            .join(sexo_view, sexo_view.c.id_sexo == Patient.id_sexo)
            .where(
                Doctor.id_user == user_id,
                Doctor.activo.is_(True),
                Patient.activo.is_(True),
                Appointment.estado.notin_(("CANCELADA", "NO_ASISTIO")),
            )
            .distinct()
            .order_by(Patient.ape_patients, Patient.nom_patients)
        )
        return self._attach_sexo_names(self.db.execute(statement).all())

    @staticmethod
    def _attach_sexo_names(results) -> list[Patient]:
        patients = []
        for patient, nom_sexo in results:
            setattr(patient, "nom_sexo", nom_sexo)
            patients.append(patient)
        return patients

    def is_assigned_to_doctor(self, patient_id: int, user_id: int) -> bool:
        statement = (
            select(Appointment.id_appointments)
            .join(Doctor, Doctor.id_doctors == Appointment.id_doctors)
            .where(
                Appointment.id_patients == patient_id,
                Doctor.id_user == user_id,
                Doctor.activo.is_(True),
                Patient.activo.is_(True),
                Appointment.estado.notin_(("CANCELADA", "NO_ASISTIO")),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def create(self, patient: Patient) -> Patient:
        try:
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
        except IntegrityError as exc:
            self.db.rollback()
            diagnostic = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "patients_document_identification" in diagnostic:
                raise ValueError(
                    "El número de identificación ya existe para este tipo de documento"
                ) from exc
            if "fk_patients_documents" in diagnostic:
                raise ValueError("El tipo de documento seleccionado no existe") from exc
            raise
        patient_with_sexo = self.get_by_id(patient.id_patients)
        if patient_with_sexo is None:
            raise RuntimeError("El paciente creado no se pudo consultar desde v_sexo")
        return patient_with_sexo

    def update(self, patient: Patient) -> Patient:
        try:
            self.db.commit()
            self.db.refresh(patient)
        except IntegrityError as exc:
            self.db.rollback()
            diagnostic = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "patients_document_identification" in diagnostic:
                raise ValueError(
                    "El número de identificación ya existe para este tipo de documento"
                ) from exc
            if "fk_patients_documents" in diagnostic:
                raise ValueError("El tipo de documento seleccionado no existe") from exc
            raise
        patient_with_sexo = self.get_by_id(patient.id_patients)
        if patient_with_sexo is None:
            raise RuntimeError("El paciente actualizado no se pudo consultar desde v_sexo")
        return patient_with_sexo

    def delete(self, patient: Patient) -> None:
        self.db.delete(patient)
        self.db.commit()
