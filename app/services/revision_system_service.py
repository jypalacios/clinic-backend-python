from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.revision_system_repository import RevisionSystemRepository


class RevisionSystemService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RevisionSystemRepository(db)

    def list_all(self) -> list[dict]:
        return self.repo.list_all()

    def create(self, detail: str, user_id: int) -> None:
        try:
            self.repo.create(detail, user_id)
            self.db.commit()
        except DBAPIError as exc:
            self.db.rollback()
            state = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
            if state == "23503":
                raise ValueError("El usuario de creación no existe.") from exc
            raise
