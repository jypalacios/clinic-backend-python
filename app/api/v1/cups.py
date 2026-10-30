from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.cup_schema import CupCreate, CupOut, CupUpdate
from app.services.cup_service import CupConflictError, CupNotFoundError, CupService

router = APIRouter(prefix="/cups", tags=["cups"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CupNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, CupConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[CupOut])
def list_cups(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permissions("cups.view")),
):
    return CupService(db).list_cups()


@router.post("/", response_model=CupOut, status_code=status.HTTP_201_CREATED)
def create_cup(
    data: CupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("cups.manage")),
):
    try:
        return CupService(db).create_cup(data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.put("/{cup_id}", response_model=CupOut)
def update_cup(
    cup_id: int,
    data: CupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("cups.manage")),
):
    try:
        return CupService(db).update_cup(cup_id, data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc
