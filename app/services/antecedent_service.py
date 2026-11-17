from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.antecedent_repository import AntecedentRepository
from app.schemas.antecedent_schema import SubAntecedentInput


class AntecedentNotFoundError(LookupError):
    pass


class AntecedentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AntecedentRepository(db)

    def save(self, data: SubAntecedentInput, user_id: int, item_id: int | None = None) -> None:
        try:
            if item_id is not None and not self.repo.lock_sub_antecedent(item_id):
                raise AntecedentNotFoundError("El subantecedente no existe.")
            self.repo.save(data, user_id, item_id)
            self.db.commit()
        except AntecedentNotFoundError:
            self.db.rollback()
            raise
        except DBAPIError as exc:
            self.db.rollback()
            state = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
            if state == "23503":
                raise ValueError("El antecedente o la especialidad no existe.") from exc
            raise
