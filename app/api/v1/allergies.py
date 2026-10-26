from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.allergy_schema import (
    AllergyCreate,
    AllergyOut,
    AllergyTypeCreate,
    AllergyTypeOut,
    AllergyTypeUpdate,
    AllergyUpdate,
)
from app.services.allergy_service import (
    AllergyConflictError,
    AllergyNotFoundError,
    AllergyService,
)

types_router = APIRouter(prefix="/allergy-types", tags=["allergy-types"])
router = APIRouter(prefix="/allergies", tags=["allergies"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AllergyNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AllergyConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@types_router.get("/", response_model=list[AllergyTypeOut])
def list_allergy_types(
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_any_permission("allergy_types.view", "allergies.view", "allergies.manage")
    ),
):
    return AllergyService(db).list_types()


@types_router.post("/", response_model=AllergyTypeOut, status_code=status.HTTP_201_CREATED)
def create_allergy_type(
    data: AllergyTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("allergy_types.manage")),
):
    try:
        return AllergyService(db).create_type(data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@types_router.put("/{type_id}", response_model=AllergyTypeOut)
def update_allergy_type(
    type_id: int,
    data: AllergyTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("allergy_types.manage")),
):
    try:
        return AllergyService(db).update_type(type_id, data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.get("/", response_model=list[AllergyOut])
def list_allergies(
    patient_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_any_permission(
            "allergies.view", "consultations.view", "medical_history.view"
        )
    ),
):
    return AllergyService(db).list_allergies(patient_id)


@router.post("/", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def create_allergy(
    data: AllergyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("allergies.manage")),
):
    try:
        return AllergyService(db).create_allergy(data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.put("/{allergy_id}", response_model=AllergyOut)
def update_allergy(
    allergy_id: int,
    data: AllergyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("allergies.manage")),
):
    try:
        return AllergyService(db).update_allergy(allergy_id, data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc
