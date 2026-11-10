from sqlalchemy import text
from sqlalchemy.orm import Session


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_types(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT id_tipo_appointment, trim(nom_tipo_appointment) AS nom_tipo_appointment "
                    "FROM v_cli_tipo_appointment ORDER BY nom_tipo_appointment, id_tipo_appointment"
                )
            ).mappings()
        ]

    def list_assignments(self, type_id: int) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(
                    "SELECT id_hc_appointment, id_tipo_appointment, "
                    "trim(nom_tipo_appointment) AS nom_tipo_appointment, id_hc_detalle, "
                    "trim(det_hc_general) AS det_hc_general FROM v_cli_hc_appointment "
                    "WHERE id_tipo_appointment = :type_id ORDER BY det_hc_general, id_hc_appointment"
                ),
                {"type_id": type_id},
            ).mappings()
        ]

    def create(self, type_id: int, detail_id: int, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_crear_cli_hc_appointment(:type_id, :detail_id, :user_id)"),
            {"type_id": type_id, "detail_id": detail_id, "user_id": user_id},
        )

    def update(self, assignment_id: int, type_id: int, detail_id: int, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_actualizar_cli_hc_appointment(:id, :detail_id, :type_id, :user_id)"),
            {"id": assignment_id, "type_id": type_id, "detail_id": detail_id, "user_id": user_id},
        )
