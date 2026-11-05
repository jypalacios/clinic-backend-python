from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.diagnosis_repository import DiagnosisRepository
from app.schemas.diagnosis_schema import DiagnosisCreate, DiagnosisUpdate

_EDITABLE_FIELDS = ("codigo", "titulo", "tipo", "nivel", "nomurl", "activo")


class DiagnosisNotFoundError(LookupError):
    pass


class DiagnosisConflictError(ValueError):
    pass


def _translate_db_error(exc: DBAPIError) -> Exception:
    """Convierte los errores levantados por los procedimientos almacenados."""
    orig = exc.orig
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    message = getattr(diag, "message_primary", None) or str(orig).splitlines()[0]
    if state == "P0002":
        return DiagnosisNotFoundError(message)
    if state == "23505":
        return DiagnosisConflictError(message)
    if state in {"23502", "22001"}:
        return ValueError(message)
    return exc


class DiagnosisService:
    def __init__(self, db: Session):
        self.repo = DiagnosisRepository(db)
        self.db = db

    def _run(self, action):
        try:
            result = action()
            self.db.commit()
            return result
        except DBAPIError as exc:
            self.db.rollback()
            translated = _translate_db_error(exc)
            if translated is exc:
                raise
            raise translated from exc

    def list_diagnoses(self) -> list[dict]:
        return self.repo.list_diagnoses()

    def create_diagnosis(self, data: DiagnosisCreate, user_id: int) -> dict:
        values = {field: getattr(data, field) for field in _EDITABLE_FIELDS}
        diag_id = self._run(lambda: self.repo.create_diagnosis(values, user_id))
        return self._require_diagnosis(diag_id)

    def update_diagnosis(self, diag_id: int, data: DiagnosisUpdate, user_id: int) -> dict:
        current = self._require_diagnosis(diag_id)
        changes = data.model_dump(exclude_unset=True)
        # El SP conserva el valor actual cuando recibe NULL, por lo que tipo/nivel/nomurl
        # solo se envían si el cliente los incluyó.
        values = {field: changes.get(field) for field in _EDITABLE_FIELDS}
        self._run(lambda: self.repo.update_diagnosis(diag_id, values, user_id))
        return self._require_diagnosis(diag_id)

    def _require_diagnosis(self, diag_id: int) -> dict:
        found = self.repo.get_diagnosis(diag_id)
        if found is None:
            raise DiagnosisNotFoundError("Diagnóstico no encontrado")
        return found
