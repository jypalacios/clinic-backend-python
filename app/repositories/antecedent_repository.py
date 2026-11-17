from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.antecedent_schema import SubAntecedentInput


class AntecedentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_antecedents(self) -> list[dict]:
        return [dict(row) for row in self.db.execute(text(
            "SELECT id_cli_antecedente, det_cli_antecedente "
            "FROM public.v_cli_antecedentes ORDER BY det_cli_antecedente, id_cli_antecedente"
        )).mappings()]

    def list_specialties(self) -> list[dict]:
        return [dict(row) for row in self.db.execute(text(
            "SELECT id_espect, nom_espect FROM public.espect ORDER BY nom_espect, id_espect"
        )).mappings()]

    def list_sub_antecedents(self) -> list[dict]:
        return [dict(row) for row in self.db.execute(text(
            "SELECT s.id_sub_antecedente, s.id_cli_antecedente, s.det_sub_antecedente, "
            "s.id_espect, a.det_cli_antecedente, e.nom_espect "
            "FROM public.cli_sub_antecedentes s "
            "JOIN public.v_cli_antecedentes a ON a.id_cli_antecedente = s.id_cli_antecedente "
            "JOIN public.espect e ON e.id_espect = s.id_espect "
            "ORDER BY a.det_cli_antecedente, e.nom_espect, s.det_sub_antecedente, s.id_sub_antecedente"
        )).mappings()]

    def lock_sub_antecedent(self, item_id: int) -> bool:
        return self.db.execute(text(
            "SELECT 1 FROM public.cli_sub_antecedentes WHERE id_sub_antecedente = :id FOR UPDATE"
        ), {"id": item_id}).first() is not None

    def save(self, data: SubAntecedentInput, user_id: int, item_id: int | None = None) -> None:
        params: dict[str, int | str] = {
            "antecedent_id": data.id_cli_antecedente,
            "detail": data.det_sub_antecedente,
            "specialty_id": data.id_espect,
            "user_id": user_id,
        }
        if item_id is None:
            sql = "CALL public.sp_crear_cli_sub_antecedentes(:antecedent_id, :detail, :specialty_id, :user_id)"
        else:
            sql = "CALL public.sp_actualizar_cli_sub_antecedentes(:id, :antecedent_id, :detail, :specialty_id, :user_id)"
            params["id"] = item_id
        self.db.execute(text(sql), params)
