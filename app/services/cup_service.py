from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.cup_repository import CupRepository
from app.schemas.cup_schema import EXTRA_FIELDS, CupCreate, CupUpdate

_EDITABLE_FIELDS = (
    "codigo",
    "nombre",
    "descripcion",
    "habilitado",
    "isstandargel",
    "isstandmsps",
    *EXTRA_FIELDS,
)


class CupNotFoundError(LookupError):
    pass


class CupConflictError(ValueError):
    pass


def _translate_db_error(exc: DBAPIError) -> Exception:
    """Convierte los errores levantados por los procedimientos almacenados."""
    orig = exc.orig
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    message = getattr(diag, "message_primary", None) or str(orig).splitlines()[0]
    if state == "P0002":
        return CupNotFoundError(message)
    if state == "23505":
        return CupConflictError(message)
    if state in {"23502", "22001"}:
        return ValueError(message)
    return exc


class CupService:
    def __init__(self, db: Session):
        self.repo = CupRepository(db)
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

    def list_cups(self) -> list[dict]:
        return self.repo.list_cups()

    def create_cup(self, data: CupCreate, user_id: int) -> dict:
        values = {field: getattr(data, field) for field in _EDITABLE_FIELDS}
        cup_id = self._run(lambda: self.repo.create_cup(values, user_id))
        return self._require_cup(cup_id)

    def update_cup(self, cup_id: int, data: CupUpdate, user_id: int) -> dict:
        current = self._require_cup(cup_id)
        changes = data.model_dump(exclude_unset=True)
        values = {
            field: changes[field] if field in changes else current[field]
            for field in _EDITABLE_FIELDS
        }
        for required in ("codigo", "nombre", "habilitado", "isstandargel", "isstandmsps"):
            if values[required] is None:
                values[required] = current[required]
        self._run(lambda: self.repo.update_cup(cup_id, values, user_id))
        return self._require_cup(cup_id)

    def _require_cup(self, cup_id: int) -> dict:
        found = self.repo.get_cup(cup_id)
        if found is None:
            raise CupNotFoundError("CUPS no encontrado")
        return found
