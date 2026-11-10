from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.clinical_record_repository import ClinicalRecordRepository
from app.schemas.analysis_schema import AnalysisAssignment


class AnalysisNotFoundError(LookupError):
    pass


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisRepository(db)

    def list_types(self) -> list[dict]:
        return self.repo.list_types()

    def list_details(self) -> list[dict]:
        return ClinicalRecordRepository(self.db).list_measure_types()

    def list_assignments(self, type_id: int) -> list[dict]:
        return self.repo.list_assignments(type_id)

    def save(self, data: AnalysisAssignment, user_id: int, assignment_id: int | None = None) -> None:
        try:
            if assignment_id is None:
                self.repo.create(data.id_tipo_appointment, data.id_hc_detalle, user_id)
            else:
                self.repo.update(assignment_id, data.id_tipo_appointment, data.id_hc_detalle, user_id)
            self.db.commit()
        except DBAPIError as exc:
            self.db.rollback()
            state = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
            if state == "23503":
                raise ValueError("El tipo de cita o el detalle de historia clínica no existe.") from exc
            if state == "P0002":
                raise AnalysisNotFoundError("La asociación no existe.") from exc
            raise
