from sqlalchemy import text
from sqlalchemy.orm import Session

DIAGNOSIS_COLUMNS = (
    "id_diag, codigo, diag_nombre, tipo, nivel, nomurl, activo, usu_creacion, "
    "usu_creacion_nombre, fec_creacion, usu_actualizacion, "
    "usu_actualizacion_nombre, fec_actualizacion"
)


class DiagnosisRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_diagnoses(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(f"SELECT {DIAGNOSIS_COLUMNS} FROM v_diagnoses ORDER BY codigo")
            ).mappings()
        ]

    def get_diagnosis(self, diag_id: int) -> dict | None:
        row = self.db.execute(
            text(f"SELECT {DIAGNOSIS_COLUMNS} FROM v_diagnoses WHERE id_diag = :id"),
            {"id": diag_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_diagnosis(self, values: dict, user_id: int) -> int:
        return self.db.execute(
            text(
                "CALL sp_insertar_cli_diagnoses(NULL, :codigo, :titulo, :tipo, "
                "CAST(:nivel AS integer), :nomurl, :activo, :user_id)"
            ),
            {**values, "user_id": user_id},
        ).scalar_one()

    def update_diagnosis(self, diag_id: int, values: dict, user_id: int) -> None:
        self.db.execute(
            text(
                "CALL sp_actualizar_cli_diagnoses(:id, :codigo, :titulo, :tipo, "
                "CAST(:nivel AS integer), :nomurl, :activo, :user_id)"
            ),
            {**values, "id": diag_id, "user_id": user_id},
        )
