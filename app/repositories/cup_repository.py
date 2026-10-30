from sqlalchemy import text
from sqlalchemy.orm import Session

CUP_COLUMNS = (
    "id_cup, codigo, nombre, descripcion, habilitado, isstandargel, isstandmsps, "
    "extra_i, extra_ii, extra_iii, extra_iv, extra_v, extra_vi, extra_vii, "
    "extra_viii, extra_ix, usu_creacion, usu_creacion_nombre, fec_creacion, "
    "usu_actualizacion, usu_actualizacion_nombre, fec_actualizacion"
)

_PROCEDURE_ARGS = (
    ":codigo, :nombre, :descripcion, :habilitado, :isstandargel, :isstandmsps, "
    ":extra_i, :extra_ii, :extra_iii, :extra_iv, :extra_v, :extra_vi, "
    ":extra_vii, :extra_viii, :extra_ix, :user_id"
)


class CupRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_cups(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(f"SELECT {CUP_COLUMNS} FROM v_cups ORDER BY codigo")
            ).mappings()
        ]

    def get_cup(self, cup_id: int) -> dict | None:
        row = self.db.execute(
            text(f"SELECT {CUP_COLUMNS} FROM v_cups WHERE id_cup = :id"),
            {"id": cup_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_cup(self, values: dict, user_id: int) -> int:
        return self.db.execute(
            text(f"CALL sp_insertar_cup(NULL, {_PROCEDURE_ARGS})"),
            {**values, "user_id": user_id},
        ).scalar_one()

    def update_cup(self, cup_id: int, values: dict, user_id: int) -> None:
        self.db.execute(
            text(f"CALL sp_actualizar_cup(:id, {_PROCEDURE_ARGS})"),
            {**values, "id": cup_id, "user_id": user_id},
        )
