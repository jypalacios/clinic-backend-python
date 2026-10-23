from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.allergy_repository import AllergyRepository
from app.schemas.allergy_schema import (
    AllergyCreate,
    AllergyTypeCreate,
    AllergyTypeUpdate,
    AllergyUpdate,
)


class AllergyNotFoundError(LookupError):
    pass


class AllergyConflictError(ValueError):
    pass


def _translate_db_error(exc: DBAPIError) -> Exception:
    """Convierte los errores levantados por los procedimientos almacenados."""
    orig = exc.orig
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    message = getattr(diag, "message_primary", None) or str(orig).splitlines()[0]
    if state == "P0002":
        return AllergyNotFoundError(message)
    if state == "23505":
        return AllergyConflictError(message)
    if state in {"23502", "22001"}:
        return ValueError(message)
    return exc


class AllergyService:
    def __init__(self, db: Session):
        self.repo = AllergyRepository(db)
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

    def list_types(self) -> list[dict]:
        return self.repo.list_types()

    def create_type(self, data: AllergyTypeCreate, user_id: int) -> dict:
        type_id = self._run(lambda: self.repo.create_type(data.nom_tipo_alergia, user_id))
        return self._require_type(type_id)

    def update_type(self, type_id: int, data: AllergyTypeUpdate, user_id: int) -> dict:
        current = self._require_type(type_id)
        changes = data.model_dump(exclude_unset=True)
        name = changes.get("nom_tipo_alergia")
        active = changes.get("activo")
        self._run(
            lambda: self.repo.update_type(
                type_id,
                current["nom_tipo_alergia"] if name is None else name,
                current["activo"] if active is None else active,
                user_id,
            )
        )
        return self._require_type(type_id)

    def list_allergies(self, patient_id: int | None = None) -> list[dict]:
        return self.repo.list_allergies(patient_id)

    def create_allergy(self, data: AllergyCreate, user_id: int) -> dict:
        allergy_id = self._run(
            lambda: self.repo.create_allergy(data.id_patients, data.id_tipo_alergia, user_id)
        )
        return self._require_allergy(allergy_id)

    def update_allergy(self, allergy_id: int, data: AllergyUpdate, user_id: int) -> dict:
        current = self._require_allergy(allergy_id)
        changes = data.model_dump(exclude_unset=True)
        type_id = changes.get("id_tipo_alergia")
        active = changes.get("activo")
        self._run(
            lambda: self.repo.update_allergy(
                allergy_id,
                current["id_tipo_alergia"] if type_id is None else type_id,
                bool(current["activo"]) if active is None else active,
                user_id,
            )
        )
        return self._require_allergy(allergy_id)

    def _require_type(self, type_id: int) -> dict:
        found = self.repo.get_type(type_id)
        if found is None:
            raise AllergyNotFoundError("Tipo de alergia no encontrado")
        return found

    def _require_allergy(self, allergy_id: int) -> dict:
        found = self.repo.get_allergy(allergy_id)
        if found is None:
            raise AllergyNotFoundError("Alergia no encontrada")
        return found
