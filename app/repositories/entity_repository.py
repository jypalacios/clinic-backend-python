from sqlalchemy import text
from sqlalchemy.orm import Session

ENTITY_COLUMNS = (
    "nit, nom_entidad, activo, usu_creacion, usu_creacion_nombre, fec_creacion, "
    "usu_actualizacion, usu_actualizacion_nombre, fec_actualizacion"
)


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_entities(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(f"SELECT {ENTITY_COLUMNS} FROM v_cli_entidades ORDER BY nom_entidad")
            ).mappings()
        ]

    def get_entity(self, nit: int) -> dict | None:
        row = self.db.execute(
            text(f"SELECT {ENTITY_COLUMNS} FROM v_cli_entidades WHERE nit = :nit"),
            {"nit": nit},
        ).mappings().first()
        return dict(row) if row else None

    def create_entity(self, nit: int, name: str, active: bool, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_insertar_entidad(:nit, :name, :active, :user_id)"),
            {"nit": nit, "name": name, "active": active, "user_id": user_id},
        )

    def update_entity(self, nit: int, name: str, active: bool, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_actualizar_entidad(:nit, :name, :active, :user_id)"),
            {"nit": nit, "name": name, "active": active, "user_id": user_id},
        )
