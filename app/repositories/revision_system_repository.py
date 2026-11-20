from sqlalchemy import text
from sqlalchemy.orm import Session


class RevisionSystemRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT id_revision_sistema, det_revision_sistemas, "
                    "usuario_creacion, usuario_modificacion "
                    "FROM public.v_cli_revision_sistemas "
                    "ORDER BY det_revision_sistemas, id_revision_sistema"
                )
            ).mappings()
        ]

    def create(self, detail: str, user_id: int) -> None:
        self.db.execute(
            text("CALL public.sp_crear_cli_revision_sistemas(:detail, :user_id)"),
            {"detail": detail, "user_id": user_id},
        )
