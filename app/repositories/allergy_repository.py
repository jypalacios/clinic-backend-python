from sqlalchemy import text
from sqlalchemy.orm import Session

TYPE_COLUMNS = (
    "id_tipo_alergia, nom_tipo_alergia, activo, usu_creacion, usuario, "
    "fec_creacion, usu_actualizacion, fec_actualizacion"
)
ALLERGY_COLUMNS = (
    "id_alergia, id_patients, ced_patients, nom_patients, ape_patients, "
    "id_tipo_alergia, nom_tipo_alergia, activo, usu_creacion, fec_creacion, "
    "usu_modificacion, fec_modificacion"
)


class AllergyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_types(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                text(f"SELECT {TYPE_COLUMNS} FROM v_tipo_alergias ORDER BY nom_tipo_alergia")
            ).mappings()
        ]

    def get_type(self, type_id: int) -> dict | None:
        row = self.db.execute(
            text(f"SELECT {TYPE_COLUMNS} FROM v_tipo_alergias WHERE id_tipo_alergia = :id"),
            {"id": type_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_type(self, name: str, user_id: int) -> int:
        return self.db.execute(
            text("CALL sp_insertar_tipo_alergia(CAST(NULL AS INTEGER), :name, :user_id)"),
            {"name": name, "user_id": user_id},
        ).scalar_one()

    def update_type(self, type_id: int, name: str, active: bool, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_actualizar_tipo_alergia(:id, :name, :active, :user_id)"),
            {"id": type_id, "name": name, "active": active, "user_id": user_id},
        )

    def list_allergies(self, patient_id: int | None = None) -> list[dict]:
        statement = f"SELECT {ALLERGY_COLUMNS} FROM v_patients_alergia"
        params: dict = {}
        if patient_id is not None:
            statement += " WHERE id_patients = :patient_id"
            params["patient_id"] = patient_id
        statement += " ORDER BY ape_patients, nom_patients, nom_tipo_alergia"
        return [dict(row) for row in self.db.execute(text(statement), params).mappings()]

    def get_allergy(self, allergy_id: int) -> dict | None:
        row = self.db.execute(
            text(f"SELECT {ALLERGY_COLUMNS} FROM v_patients_alergia WHERE id_alergia = :id"),
            {"id": allergy_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_allergy(self, patient_id: int, type_id: int, user_id: int) -> int:
        return self.db.execute(
            text(
                "CALL sp_insertar_alergias(CAST(NULL AS INTEGER), :patient_id, :type_id, :user_id)"
            ),
            {"patient_id": patient_id, "type_id": type_id, "user_id": user_id},
        ).scalar_one()

    def update_allergy(self, allergy_id: int, type_id: int, active: bool, user_id: int) -> None:
        self.db.execute(
            text("CALL sp_actualizar_alergia(:id, :type_id, :active, :user_id)"),
            {"id": allergy_id, "type_id": type_id, "active": active, "user_id": user_id},
        )
