from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission
from app.db.session import get_db
from app.models.sexo import Sexo
from app.schemas.sexo_schema import SexoOut

router = APIRouter(prefix="/sexos", tags=["sexos"])


@router.get("/", response_model=list[SexoOut])
def list_sexos(
    db: Session = Depends(get_db),
    _current_user=Depends(
        require_any_permission("patients.view", "doctors.view", "patients.manage", "doctors.manage")
    ),
) -> list[Sexo]:
    return db.query(Sexo).order_by(Sexo.id_sexo).all()
