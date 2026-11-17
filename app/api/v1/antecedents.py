from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.repositories.antecedent_repository import AntecedentRepository
from app.schemas.antecedent_schema import AntecedentOut, AntecedentSpecialtyOut, SubAntecedentInput, SubAntecedentOut
from app.services.antecedent_service import AntecedentNotFoundError, AntecedentService

router = APIRouter(prefix="/antecedents", tags=["antecedents"])


@router.get("", response_model=list[AntecedentOut])
def list_antecedents(db: Session = Depends(get_db), _user: User = Depends(require_permissions("antecedents.view"))):
    return AntecedentRepository(db).list_antecedents()


@router.get("/specialties", response_model=list[AntecedentSpecialtyOut])
def list_specialties(db: Session = Depends(get_db), _user: User = Depends(require_permissions("antecedents.view"))):
    return AntecedentRepository(db).list_specialties()


@router.get("/items", response_model=list[SubAntecedentOut])
def list_items(db: Session = Depends(get_db), _user: User = Depends(require_permissions("antecedents.view"))):
    return AntecedentRepository(db).list_sub_antecedents()


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(data: SubAntecedentInput, db: Session = Depends(get_db), user: User = Depends(require_permissions("antecedents.manage"))):
    try:
        AntecedentService(db).save(data, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Subantecedente creado correctamente."}


@router.put("/items/{item_id}")
def update_item(data: SubAntecedentInput, item_id: int = Path(gt=0), db: Session = Depends(get_db), user: User = Depends(require_permissions("antecedents.manage"))):
    try:
        AntecedentService(db).save(data, user.id, item_id)
    except AntecedentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Subantecedente actualizado correctamente."}
