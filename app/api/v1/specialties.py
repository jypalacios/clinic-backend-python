from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.schemas.specialty_schema import SpecialtyCreate, SpecialtyOut
from app.services.specialty_service import SpecialtyService

router = APIRouter(prefix="/specialties", tags=["specialties"])


@router.get(
    "/",
    response_model=list[SpecialtyOut],
    dependencies=[Depends(require_any_permission("specialties.view", "doctors.view", "doctors.manage"))],
)
def list_specialties(
    db: Session = Depends(get_db),
) -> list[SpecialtyOut]:
    return SpecialtyService(db).list_specialties()


@router.post(
    "/",
    response_model=SpecialtyOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("specialties.manage"))],
)
def create_specialty(
    data: SpecialtyCreate,
    db: Session = Depends(get_db),
) -> SpecialtyOut:
    try:
        return SpecialtyService(db).create_specialty(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
