from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.schemas.role_schema import RoleCreate, RoleOut, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _current_user=Depends(require_any_permission("users.view", "roles.manage")),
):
    return RoleService(db).list_roles()


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).create_role(data, created_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).update_role(role_id, data, updated_by=current_user.id)
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if str(exc) == "Rol no encontrado" else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
