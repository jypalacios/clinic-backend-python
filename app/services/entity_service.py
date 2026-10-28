from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.entity_repository import EntityRepository
from app.schemas.entity_schema import EntityCreate, EntityUpdate


class EntityNotFoundError(LookupError):
    pass


class EntityConflictError(ValueError):
    pass


def _translate_db_error(exc: DBAPIError) -> Exception:
    """Convierte los errores levantados por los procedimientos almacenados."""
    orig = exc.orig
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    message = getattr(diag, "message_primary", None) or str(orig).splitlines()[0]
    if state == "P0002":
        return EntityNotFoundError(message)
    if state == "23505":
        return EntityConflictError(message)
    if state in {"23502", "22001"}:
        return ValueError(message)
    return exc


class EntityService:
    def __init__(self, db: Session):
        self.repo = EntityRepository(db)
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

    def list_entities(self) -> list[dict]:
        return self.repo.list_entities()

    def create_entity(self, data: EntityCreate, user_id: int) -> dict:
        self._run(
            lambda: self.repo.create_entity(data.nit, data.nom_entidad, data.activo, user_id)
        )
        return self._require_entity(data.nit)

    def update_entity(self, nit: int, data: EntityUpdate, user_id: int) -> dict:
        current = self._require_entity(nit)
        changes = data.model_dump(exclude_unset=True)
        name = changes.get("nom_entidad")
        active = changes.get("activo")
        self._run(
            lambda: self.repo.update_entity(
                nit,
                current["nom_entidad"] if name is None else name,
                bool(current["activo"]) if active is None else active,
                user_id,
            )
        )
        return self._require_entity(nit)

    def _require_entity(self, nit: int) -> dict:
        found = self.repo.get_entity(nit)
        if found is None:
            raise EntityNotFoundError("Entidad no encontrada")
        return found
