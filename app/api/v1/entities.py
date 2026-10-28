from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.entity_schema import EntityCreate, EntityOut, EntityUpdate
from app.services.entity_service import (
    EntityConflictError,
    EntityNotFoundError,
    EntityService,
)

router = APIRouter(prefix="/entities", tags=["entities"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, EntityNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, EntityConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[EntityOut])
def list_entities(
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_any_permission(
            "entities.view", "patients.manage", "patients.edit", "patients.view"
        )
    ),
):
    return EntityService(db).list_entities()


@router.post("/", response_model=EntityOut, status_code=status.HTTP_201_CREATED)
def create_entity(
    data: EntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("entities.manage")),
):
    try:
        return EntityService(db).create_entity(data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.put("/{nit}", response_model=EntityOut)
def update_entity(
    nit: int,
    data: EntityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("entities.manage")),
):
    try:
        return EntityService(db).update_entity(nit, data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc
